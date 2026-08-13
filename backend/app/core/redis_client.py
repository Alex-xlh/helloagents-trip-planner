"""Redis 缓存客户端管理器"""

import redis.asyncio as redis
from typing import Optional
from loguru import logger
from ..config import get_settings

# 全局 Redis 连接池实例
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端，懒加载单例模式"""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client

async def close_redis_client():
    """关闭 Redis 客户端连接"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
        logger.info("Redis 连接已安全释放")

async def get_cache(key: str) -> Optional[str]:
    """从 Redis 获取缓存内容"""
    try:
        client = get_redis_client()
        return await client.get(key)
    except Exception as e:
        logger.warning(f"Redis 读取缓存失败: {e}")
        return None

async def set_cache(key: str, value: str, expire: int = 86400):
    """将内容写入 Redis 缓存，默认过期时间 24 小时 (86400 秒)"""
    try:
        client = get_redis_client()
        await client.setex(key, expire, value)
    except Exception as e:
        logger.warning(f"Redis 写入缓存失败: {e}")
