"""多智能体旅行规划系统 (基于 LangChain / LangGraph)"""

import json
import asyncio
from typing import Dict, Any, List
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
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
1. 每天【严格】安排 2-3 个核心景点（**绝对不可超过 3 个**，留出充足的休息时间！）
2. 每天必须包含早中晚三餐
3. 每天推荐一个具体的酒店(从酒店信息中选择)
4. 考虑景点之间的距离和交通方式
5. **【致命纪律】景点的经纬度坐标必须真实准确！你【只能】从提供的【景点信息】和【酒店信息】列表中挑选地点。严禁自己编造任何未在列表中出现的景点或酒店名称及坐标！**
6. **必须包含预算信息**(门票、餐饮、住宿及总预算)
"""

GREETING_AGENT_PROMPT = """你是专属旅行预热管家。当用户准备前往 {city} 时，你需要写一段 150 字左右的开场白，热情介绍该城市的特色风土人情，并明确告诉用户“我正在后台为您极速调取高德地图和天气数据，并为您精心编织行程，请稍候...”。语气要非常高端、优雅、亲切。直接使用纯文本或 Markdown 输出，不需要任何真实的数据。"""

INTENT_ROUTER_PROMPT = """你是核心意图提取器。
用户的附加要求为：【{free_text_input}】。

你的唯一任务是：判断用户是否在附加要求中，明确指定了必须要去的**具体专有名词（如特定的景点名、酒店名、餐厅名、地名）**。
你必须且只能输出一个 JSON 对象，严禁输出任何多余的解释文本或 markdown 格式块。结构严格如下：
{{
  "must_fetch_pois": ["提取出的具体专有名词，例如'欢乐谷'、'全聚德'。如果没有明确指定具体地名，则返回空数组 []"]
}}
"""




class MultiAgentTripPlanner:
    """多智能体旅行规划系统 (LangChain)"""

    def __init__(self):
        """初始化多智能体系统"""
        print("🔄 开始初始化多智能体旅行规划系统(LangChain)...")

        try:
            self.llm = get_llm()

            # 1. 景点、天气、酒店 Agent 已移除 (升级为 Agentic Workflow，直接底层并发调用工具)

            # 2. 预热管家 Greeting Agent (直接 Chain)
            self.greeting_chain = ChatPromptTemplate.from_template(GREETING_AGENT_PROMPT) | self.llm

            # 3. 意图路由器 Router Agent
            self.router_chain = ChatPromptTemplate.from_template(INTENT_ROUTER_PROMPT) | self.llm | JsonOutputParser()


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
                import time
                
                # --- A. 意图解析 (Router Agent) ---
                print("🧠 [Router Agent] 开始极速解析意图...")
                router_start = time.time()
                prefs_joined = " ".join(request.preferences) if request.preferences else "无特殊偏好"
                extra_reqs = request.free_text_input if request.free_text_input else "无"
                try:
                    intent_data = await self.router_chain.ainvoke({
                        "city": request.city,
                        "preferences": prefs_joined,
                        "free_text_input": extra_reqs
                    })
                except Exception as e:
                    print(f"⚠️ [Router Agent] 解析失败，使用默认退化策略: {e}")
                    intent_data = {
                        "must_fetch_pois": []
                    }
                router_end = time.time()
                print(f"⏱️ [Router Agent] 意图解析耗时: {router_end - router_start:.2f} 秒. 提取结果: {intent_data}")

                # --- B. 数据抓取 (Python Script) ---
                async def fetch_attractions():
                    start_t = time.time()
                    
                    # 1. 抓取基础推荐标签 (直接使用用户的 preferences)
                    tags_str = " ".join(request.preferences) if request.preferences else "著名景点"
                    
                    # 使用 asyncio.gather 并发抓取“偏好推荐”和“必去清单”
                    tasks = [amap_maps_text_search.ainvoke({"keywords": tags_str, "city": request.city})]
                    
                    # 2. 对每个必去地点额外派发抓取任务，确保绝对命中
                    must_visits = intent_data.get("must_fetch_pois", [])
                    for mv in must_visits:
                        tasks.append(amap_maps_text_search.ainvoke({"keywords": mv, "city": request.city}))
                    
                    results = await asyncio.gather(*tasks)
                    # 简单拼接所有返回内容
                    combined_res = "\n\n".join(results)
                    
                    end_t = time.time()
                    print(f"⏱️ [Attraction Tool] 景点直调抓取耗时: {end_t - start_t:.2f} 秒 (包含必去清单)")
                    return combined_res

                async def fetch_weather():
                    start_t = time.time()
                    res = await amap_maps_weather.ainvoke({"city": request.city})
                    end_t = time.time()
                    print(f"⏱️ [Weather Tool] 天气直调查询耗时: {end_t - start_t:.2f} 秒")
                    return res

                async def fetch_hotels():
                    start_t = time.time()
                    hotel_keywords = f"{request.accommodation} 酒店"
                    res = await amap_maps_text_search.ainvoke({"keywords": hotel_keywords, "city": request.city})
                    end_t = time.time()
                    print(f"⏱️ [Hotel Tool] 酒店直调搜索耗时: {end_t - start_t:.2f} 秒")
                    return res

                # 并发收集数据
                gather_start = time.time()
                attraction_response, weather_response, hotel_response = await asyncio.gather(
                    fetch_attractions(),
                    fetch_weather(),
                    fetch_hotels()
                )
                gather_end = time.time()
                print(f"🔥 [并发总耗时] 3大前置 Agent 执行完毕共计耗时: {gather_end - gather_start:.2f} 秒")

                # --- C. 行程规划 (Planner Agent) ---
                # 核心排版 LLM
                parser = PydanticOutputParser(pydantic_object=TripPlan)
                prompt_planner = ChatPromptTemplate.from_template(
                    PLANNER_AGENT_PROMPT + "\n\n{format_instructions}"
                )
                planner_chain = prompt_planner | self.llm | parser

                # 把原始附加条件完整传给 planner
                print(f"🧠 [Planner Agent] 开始执行最终规划...")
                planner_start = time.time()
                trip_plan = await planner_chain.ainvoke({
                    "city": request.city,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                    "travel_days": request.travel_days,
                    "transportation": request.transportation,
                    "accommodation": request.accommodation,
                    "preferences": prefs_joined,
                    "extra_reqs": f"特殊要求：{extra_reqs}",
                    "attractions": attraction_response,
                    "weather": weather_response,
                    "hotels": hotel_response,
                    "format_instructions": parser.get_format_instructions()
                })
                planner_end = time.time()
                print(f"🎯 [Planner Agent] 最终行程规划生成耗时: {planner_end - planner_start:.2f} 秒")
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
