"""多智能体旅行规划系统 (基于 LangChain / LangGraph)"""

import json
import asyncio
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

PLANNER_AGENT_PROMPT = """你是高端旅行规划专家。你的任务是根据给定的景点、天气和酒店信息，生成极具吸引力的定制旅行计划。

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

GREETING_AGENT_PROMPT = """你是专属旅行预热管家。当用户准备前往 {city} 时，你需要写一段 150 字左右的开场白，热情介绍该城市的特色风土人情，并明确告诉用户“我正在后台为您极速调取高德地图和天气数据，并为您精心编织行程，请稍候...”。语气要非常高端、优雅、亲切。直接使用纯文本或 Markdown 输出，不需要任何真实的数据。"""




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

            # 4. 预热管家 Greeting Agent (直接 Chain)
            self.greeting_chain = ChatPromptTemplate.from_template(GREETING_AGENT_PROMPT) | self.llm


            print(f"✅ 多智能体系统初始化成功 (LangChain)")

        except Exception as e:
            print(f"❌ 多智能体系统初始化失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    


    async def plan_trip_stream(self, request: TripRequest):
        """流式生成旅行计划(双轨并发: 预热打字机 + 后台调高德核心引擎)"""
        try:
            print(f"\n{'='*60}")
            print(f"🚀 开始多智能体协作流式规划旅行(双轨并发)...")
            print(f"目的地: {request.city}")
            print(f"天数: {request.travel_days}天")
            print(f"{'='*60}\n")

            # === 定义后台计算任务 ===
            async def fetch_and_plan():
                keywords = request.preferences[0] if request.preferences else "景点"
                attraction_query = f"请搜索{request.city}的{keywords}相关景点"
                weather_query = f"请查询{request.city}的天气信息"
                hotel_query = f"请搜索{request.city}的{request.accommodation}酒店"

                async def fetch_attractions():
                    res = await self.attraction_agent.ainvoke({"messages": [("human", attraction_query)]})
                    return res["messages"][-1].content

                async def fetch_weather():
                    res = await self.weather_agent.ainvoke({"messages": [("human", weather_query)]})
                    return res["messages"][-1].content

                async def fetch_hotels():
                    res = await self.hotel_agent.ainvoke({"messages": [("human", hotel_query)]})
                    return res["messages"][-1].content

                # 并发收集数据
                attraction_response, weather_response, hotel_response = await asyncio.gather(
                    fetch_attractions(),
                    fetch_weather(),
                    fetch_hotels()
                )

                # 核心排版 LLM
                parser = PydanticOutputParser(pydantic_object=TripPlan)
                prompt_planner = ChatPromptTemplate.from_template(
                    PLANNER_AGENT_PROMPT + "\n\n{format_instructions}"
                )
                extra_reqs = f"\n**额外要求:** {request.free_text_input}" if request.free_text_input else ""
                prefs = ', '.join(request.preferences) if request.preferences else '无'
                
                planner_chain = prompt_planner | self.llm | parser
                trip_plan = await planner_chain.ainvoke({
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
                return trip_plan

            # 🚀 1. 立即启动后台繁重的计算任务 (不 await, 扔到后台去跑)
            planner_task = asyncio.create_task(fetch_and_plan())

            # 🚀 2. 立即在前台触发 Greeting Agent，直接开始打字机
            async for chunk in self.greeting_chain.astream({"city": request.city}):
                if chunk.content:
                    yield chunk.content
            
            # 🚀 3. 打字机打完了，此时静静等待后台任务（其实大部分时候后台已经跑完了，实现了零感知等待）
            yield "\n\n*(高德数据已就绪，正在生成精美行程单...)*\n\n"
            trip_plan = await planner_task
            
            # 🚀 4. 将结果包裹成前端需要的 JSON 格式吐出，触发前端跳转
            yield f"\n\n```json\n{trip_plan.model_dump_json()}\n```\n"
            
        except Exception as e:
            print(f"❌ 流式生成旅行计划失败: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"\n\n生成失败: {str(e)}"
    
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
