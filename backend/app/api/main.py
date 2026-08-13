"""FastAPI主应用"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from ..config import get_settings, validate_config, print_config
from .routes import trip, poi, auth, history
from ..services.amap_service import init_mcp_client, close_mcp_client
from ..core.http_client import init_http_client, close_http_client
from ..core.redis_client import close_redis_client
from ..core.database import engine
from ..models.db import Base
from ..core.logging import setup_logging
from loguru import logger
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from ..core.limiter import limiter
from fastapi.staticfiles import StaticFiles
import os

# 获取配置
settings = get_settings()
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # === 启动时执行的逻辑 (Startup) ===
    logger.info(f"{settings.app_name} v{settings.app_version} 启动中")
    
    # 打印配置信息
    print_config()
    
    # 验证配置
    try:
        validate_config()
        logger.info("配置验证通过")
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        logger.error("请检查.env文件并确保所有必要的配置项都已设置")
        raise
    
    logger.info("API文档: http://localhost:8000/docs")
    logger.info("ReDoc文档: http://localhost:8000/redoc")
    
    # 初始化全局MCP长连接池
    try:
        await init_mcp_client()
    except Exception as e:
        logger.warning(f"MCP长连接池初始化失败，将降级为请求时初始化: {e}")
        
    # 初始化全局 HTTP 连接池
    try:
        await init_http_client()
    except Exception as e:
        logger.error(f"HTTP 连接池初始化失败: {e}")
        
    # 初始化数据库
    try:
        async with engine.begin() as conn:
            # 在实际生产中应该使用 alembic 进行迁移，这里简单创建表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表初始化成功")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
    
    yield # 让应用开始处理请求
    
    # === 关闭时执行的逻辑 (Shutdown) ===
    logger.info("应用正在关闭")
    
    # 释放全局MCP长连接资源
    try:
        await close_mcp_client()
    except Exception as e:
        logger.warning(f"释放MCP长连接资源失败: {e}")

    # 释放全局 HTTP 连接池
    try:
        await close_http_client()
    except Exception as e:
        logger.warning(f"释放HTTP长连接资源失败: {e}")

    # 释放 Redis 连接资源
    try:
        await close_redis_client()
    except Exception as e:
        logger.warning(f"释放Redis连接资源失败: {e}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于langchain框架的智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 注册限流器
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    #白名单
    allow_origins=settings.get_cors_origins_list(),
    #允许携带cookie
    allow_credentials=True,
    #允许的方法，所有
    allow_methods=["*"],
    #允许的请求头，所有
    allow_headers=["*"],
)

# 确保 static 目录存在
os.makedirs("static/tts", exist_ok=True)
# 挂载静态文件目录，用于返回音频文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(history.router, prefix="/api")
from .routes import tts
from .routes import guide
app.include_router(tts.router, prefix="/api")
app.include_router(guide.router, prefix="/api")

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
