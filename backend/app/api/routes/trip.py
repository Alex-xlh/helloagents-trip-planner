"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ...models.schemas import (
    TripRequest,
)
from ...agents.trip_planner_agent import get_trip_planner_agent

router = APIRouter(prefix="/trip", tags=["旅行规划"])




import hashlib
import json
import asyncio
from loguru import logger
from ...core.redis_client import get_cache, set_cache
from ...core.limiter import limiter

def generate_cache_key(request: TripRequest) -> str:
    """基于请求参数生成唯一的 MD5 缓存键"""
    req_dict = request.model_dump()
    req_str = json.dumps(req_dict, sort_keys=True)
    return "trip_cache:" + hashlib.md5(req_str.encode()).hexdigest()

@router.post(
    "/plan/stream",
    summary="流式生成旅行计划",
    description="流式返回打字机效果文字及最终JSON"
)
@limiter.limit("3/minute")
@limiter.limit("20/hour")
async def plan_trip_stream_route(request: Request, trip_request: TripRequest):
    """流式生成旅行计划 (Server-Sent Events / 文本流)"""
    try:
        logger.info(f"收到流式旅行规划请求: 城市={trip_request.city}")
        
        # 1. 生成 Cache Key 并查询 Redis
        cache_key = generate_cache_key(trip_request)
        cached_result = await get_cache(cache_key)
        
        if cached_result:
            logger.info("命中 Redis 行程缓存，直接返回缓存流")
            async def cached_text_generator():
                # 按照 50 个字符为一块，极速模拟打字机，实现流式输出的震撼感
                chunk_size = 50
                for i in range(0, len(cached_result), chunk_size):
                    yield cached_result[i:i+chunk_size]
                    await asyncio.sleep(0.01) # 极快速度流出
            return StreamingResponse(cached_text_generator(), media_type="text/plain; charset=utf-8")
        
        logger.info("未命中 Redis 行程缓存，开始调用大模型规划")
        agent = get_trip_planner_agent()
        
        async def text_generator():
            full_response_buffer = []
            try:
                async for chunk in agent.plan_trip_stream(trip_request):
                    full_response_buffer.append(chunk)
                    yield chunk
                
                # 流式输出结束后，将完整结果拼合存入 Redis
                final_text = "".join(full_response_buffer)
                await set_cache(cache_key, final_text)
                logger.info("行程生成完毕，已回填 Redis 缓存")
                
            except Exception as e:
                logger.exception(f"流式生成旅行计划失败: {e}")
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
