from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from ..config import get_settings

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database_url

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 获取数据库会话的依赖函数
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
