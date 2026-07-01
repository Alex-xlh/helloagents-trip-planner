import httpx
from typing import Optional

# 全局 HTTP 客户端，支持连接池复用
_http_client: Optional[httpx.AsyncClient] = None

def get_http_client() -> httpx.AsyncClient:
    """获取全局 HTTP 客户端实例"""
    global _http_client
    if _http_client is None:
        raise RuntimeError("HTTP Client is not initialized. Call init_http_client() first.")
    return _http_client

async def init_http_client():
    """初始化全局 HTTP 客户端（在 FastAPI lifespan 启动时调用）"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=15.0,
            limits=httpx.Limits(max_keepalive_connections=50, max_connections=100)
        )
        print("✅ HTTP 并发连接池初始化成功")

async def close_http_client():
    """关闭全局 HTTP 客户端（在 FastAPI lifespan 关闭时调用）"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
        print("🧹 HTTP 并发连接池已安全释放")
