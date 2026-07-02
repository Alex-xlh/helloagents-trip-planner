"""Redis 缓存客户端管理器"""

import json
import redis.asyncio as redis
from typing import Optional

# 全局 Redis 连接池实例
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端，懒加载单例模式"""
    global _redis_client
    if _redis_client is None:
        # TODO: 在生产环境中应当从环境变量读取 URL
        _redis_client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    return _redis_client

async def get_cache(key: str) -> Optional[str]:
    """从 Redis 获取缓存内容"""
    try:
        client = get_redis_client()
        return await client.get(key)
    except Exception as e:
        print(f"⚠️ Redis 读取缓存失败: {e}")
        return None

async def set_cache(key: str, value: str, expire: int = 86400):
    """将内容写入 Redis 缓存，默认过期时间 24 小时 (86400 秒)"""
    try:
        client = get_redis_client()
        await client.setex(key, expire, value)
    except Exception as e:
        print(f"⚠️ Redis 写入缓存失败: {e}")
