from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 数据库文件保存在根目录下
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./trips.db"

# 创建异步引擎
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, 
    echo=False, 
    # check_same_thread=False is needed only for SQLite
    connect_args={"check_same_thread": False}
)

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 获取数据库会话的依赖函数
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
