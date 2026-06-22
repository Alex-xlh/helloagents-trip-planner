"""FastAPI主应用"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from ..config import get_settings, validate_config, print_config
from .routes import trip, poi, map as map_routes
from ..services.amap_service import init_mcp_client, close_mcp_client

# 获取配置
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理器"""
    # === 启动时执行的逻辑 (Startup) ===
    print("\n" + "="*60)
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print("="*60)
    
    # 打印配置信息
    print_config()
    
    # 验证配置
    try:
        validate_config()
        print("\n✅ 配置验证通过")
    except ValueError as e:
        print(f"\n❌ 配置验证失败:\n{e}")
        print("\n请检查.env文件并确保所有必要的配置项都已设置")
        raise
    
    print("\n" + "="*60)
    print("📚 API文档: http://localhost:8000/docs")
    print("📖 ReDoc文档: http://localhost:8000/redoc")
    print("="*60 + "\n")
    
    # 初始化全局MCP长连接池
    try:
        await init_mcp_client()
    except Exception as e:
        print(f"⚠️ MCP长连接池初始化失败，将降级为请求时初始化: {e}")
    
    yield # 让应用开始处理请求
    
    # === 关闭时执行的逻辑 (Shutdown) ===
    print("\n" + "="*60)
    print("👋 应用正在关闭...")
    print("="*60 + "\n")
    
    # 释放全局MCP长连接资源
    try:
        await close_mcp_client()
    except Exception as e:
        print(f"⚠️ 释放MCP长连接资源失败: {e}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于langchain框架的智能旅行规划助手API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

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

# 注册路由
app.include_router(trip.router, prefix="/api")
app.include_router(poi.router, prefix="/api")
app.include_router(map_routes.router, prefix="/api")

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
