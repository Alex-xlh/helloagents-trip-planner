"""多智能体旅行规划系统 (基于 LangChain / LangGraph)"""

import json
from typing import Dict, Any, List
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import ValidationError

from ..services.llm_service import get_llm
from ..services.amap_service import amap_maps_text_search, amap_maps_weather
from ..models.schemas import TripRequest, TripPlan, DayPlan, Attraction, Meal, WeatherInfo, Location, Hotel
from ..config import get_settings

# ============ Agent提示词 ============

ATTRACTION_AGENT_PROMPT = """你是景点搜索专家。你的任务是根据城市和用户偏好搜索合适的景点。
请使用 `amap_maps_text_search` 工具来搜索景点。必须返回搜索结果的具体信息，不要自己编造。
"""

WEATHER_AGENT_PROMPT = """你是天气查询专家。你的任务是查询指定城市的天气信息。
请使用 `amap_maps_weather` 工具来查询天气。必须返回搜索结果的具体信息，不要自己编造。
"""

HOTEL_AGENT_PROMPT = """你是酒店推荐专家。你的任务是根据城市和景点位置推荐合适的酒店。
请使用 `amap_maps_text_search` 工具搜索酒店(关键词使用"酒店"或"宾馆")。必须返回搜索结果的具体信息，不要自己编造。
"""

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据给定的景点、天气和酒店信息，生成详细的旅行计划。

**基本信息:**
- 城市: {city}
- 日期: {start_date} 至 {end_date}
- 天数: {travel_days}天
- 交通方式: {transportation}
- 住宿: {accommodation}
- 偏好: {preferences}
{extra_reqs}

**景点信息:**
{attractions}

**天气信息:**
{weather}

**酒店信息:**
{hotels}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
4. 考虑景点之间的距离和交通方式
5. 景点的经纬度坐标要真实准确
6. **必须包含预算信息**(门票、餐饮、住宿及总预算)
"""


class MultiAgentTripPlanner:
    """多智能体旅行规划系统 (LangChain)"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统(LangChain)...")

        try:
            self.llm = get_llm()

            # 1. 景点搜索 Agent
            self.attraction_agent = create_react_agent(self.llm, tools=[amap_maps_text_search], prompt=ATTRACTION_AGENT_PROMPT)

            # 2. 天气查询 Agent
            self.weather_agent = create_react_agent(self.llm, tools=[amap_maps_weather], prompt=WEATHER_AGENT_PROMPT)

            # 3. 酒店推荐 Agent
            self.hotel_agent = create_react_agent(self.llm, tools=[amap_maps_text_search], prompt=HOTEL_AGENT_PROMPT)



            print(f"✅ 多智能体系统初始化成功 (LangChain)")

        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def plan_trip(self, request: TripRequest) -> TripPlan:
        """使用多智能体协作生成旅行计划"""
        try:
            print(f"\n{'='*60}")
            print(f"🚀 开始多智能体协作规划旅行(LangChain)...")
            print(f"目的地: {request.city}")
            print(f"日期: {request.start_date} 至 {request.end_date}")
            print(f"天数: {request.travel_days}天")
            print(f"偏好: {', '.join(request.preferences) if request.preferences else '无'}")
            print(f"{'='*60}\n")

            # 步骤1: 搜索景点
            print("📍 步骤1: 搜索景点...")
            keywords = request.preferences[0] if request.preferences else "景点"
            attraction_query = f"请搜索{request.city}的{keywords}相关景点"
            attraction_res = self.attraction_agent.invoke({"messages": [("human", attraction_query)]})
            attraction_response = attraction_res["messages"][-1].content
            print(f"景点搜索结果: {attraction_response[:200]}...\n")

            # 步骤2: 查询天气
            print("🌤️  步骤2: 查询天气...")
            weather_query = f"请查询{request.city}的天气信息"
            weather_res = self.weather_agent.invoke({"messages": [("human", weather_query)]})
            weather_response = weather_res["messages"][-1].content
            print(f"天气查询结果: {weather_response[:200]}...\n")

            # 步骤3: 搜索酒店
            print("🏨 步骤3: 搜索酒店...")
            hotel_query = f"请搜索{request.city}的{request.accommodation}酒店"
            hotel_res = self.hotel_agent.invoke({"messages": [("human", hotel_query)]})
            hotel_response = hotel_res["messages"][-1].content
            print(f"酒店搜索结果: {hotel_response[:200]}...\n")

            # 4. 行程规划 LLM
            # 不使用 with_structured_output 因为部分模型不支持 response_format
            parser = PydanticOutputParser(pydantic_object=TripPlan)
            prompt_planner = ChatPromptTemplate.from_template(
                PLANNER_AGENT_PROMPT + "\n\n{format_instructions}"
            )
            extra_reqs = f"\n**额外要求:** {request.free_text_input}" if request.free_text_input else ""
            prefs = ', '.join(request.preferences) if request.preferences else '无'
            
            planner_chain = prompt_planner | self.llm | parser
            trip_plan = planner_chain.invoke({
                "city": request.city,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "travel_days": request.travel_days,
                "transportation": request.transportation,
                "accommodation": request.accommodation,
                "preferences": prefs,
                "extra_reqs": extra_reqs,
                "attractions": attraction_response,
                "weather": weather_response,
                "hotels": hotel_response,
                "format_instructions": parser.get_format_instructions()
            })
            
            print(f"{'='*60}")
            print(f"✅ 旅行计划生成完成!")
            print(f"{'='*60}\n")

            return trip_plan

        except Exception as e:
            print(f"❌ 生成旅行计划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_fallback_plan(request)
    
    def _create_fallback_plan(self, request: TripRequest) -> TripPlan:
        """创建备用计划(当Agent失败时)"""
        from datetime import datetime, timedelta
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        days = []
        for i in range(request.travel_days):
            current_date = start_date + timedelta(days=i)
            day_plan = DayPlan(
                date=current_date.strftime("%Y-%m-%d"),
                day_index=i,
                description=f"第{i+1}天行程",
                transportation=request.transportation,
                accommodation=request.accommodation,
                attractions=[
                    Attraction(
                        name=f"{request.city}景点{j+1}",
                        address=f"{request.city}市",
                        location=Location(longitude=116.4 + i*0.01 + j*0.005, latitude=39.9 + i*0.01 + j*0.005),
                        visit_duration=120,
                        description=f"这是{request.city}的著名景点",
                        category="景点"
                    )
                    for j in range(2)
                ],
                meals=[
                    Meal(type="breakfast", name=f"第{i+1}天早餐", description="当地特色早餐"),
                    Meal(type="lunch", name=f"第{i+1}天午餐", description="午餐推荐"),
                    Meal(type="dinner", name=f"第{i+1}天晚餐", description="晚餐推荐")
                ]
            )
            days.append(day_plan)
        
        return TripPlan(
            city=request.city,
            start_date=request.start_date,
            end_date=request.end_date,
            days=days,
            weather_info=[],
            overall_suggestions=f"这是为您规划的{request.city}{request.travel_days}日游行程,建议提前查看各景点的开放时间。"
        )

# 全局多智能体系统实例
_multi_agent_planner = None

def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取多智能体旅行规划系统实例(单例模式)"""
    global _multi_agent_planner
    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()
    return _multi_agent_planner
