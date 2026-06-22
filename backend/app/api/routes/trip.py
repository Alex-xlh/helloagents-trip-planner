"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ...models.schemas import (
    TripRequest,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent

router = APIRouter(prefix="/trip", tags=["旅行规划"])




@router.post(
    "/plan/stream",
    summary="流式生成旅行计划",
    description="流式返回打字机效果文字及最终JSON"
)
async def plan_trip_stream_route(request: TripRequest):
    """
    流式生成旅行计划 (Server-Sent Events / 文本流)
    """
    try:
        print(f"\n{'='*60}")
        print(f"📥 收到流式旅行规划请求:")
        print(f"   城市: {request.city}")
        print(f"{'='*60}\n")

        agent = get_trip_planner_agent()
        
        async def text_generator():
            try:
                async for chunk in agent.plan_trip_stream(request):
                    yield chunk
            except Exception as e:
                yield f"\n\n[服务器错误]: {str(e)}"
                
        # 返回原生文本流
        return StreamingResponse(text_generator(), media_type="text/plain; charset=utf-8")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"流式生成旅行计划失败: {str(e)}"
        )


@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
async def health_check():
    """健康检查"""
    try:
        # 检查Agent是否可用
        agent = get_trip_planner_agent()
        
        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": "MultiAgentTripPlanner",
            "tools_count": 3
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )

