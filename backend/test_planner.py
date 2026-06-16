import os
import sys
import asyncio

# 添加到系统路径以导入应用模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import TripRequest
from app.agents.trip_planner_agent import get_trip_planner_agent

def main():
    try:
        agent = get_trip_planner_agent()
        print("Agent acquired successfully.")
        
        request = TripRequest(
            city="北京",
            start_date="2026-07-01",
            end_date="2026-07-03",
            travel_days=3,
            transportation="地铁和打车",
            accommodation="高档",
            preferences=["历史文化", "美食"],
            free_text_input="不要行程太紧"
        )
        
        plan = agent.plan_trip(request)
        print("\n\n====== 最终计划 ======")
        print(plan.model_dump_json(indent=2))
        print("======================")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
