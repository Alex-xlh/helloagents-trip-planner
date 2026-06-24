from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, field_validator

from ...core.database import get_db
from ...core.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_user
)
from ...models.db import User
from ...core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    username: str
    password: str

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('密码长度不能少于6位')
        if v.isdigit():
            raise ValueError('密码不能为纯数字')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError('用户名长度不能少于2位')
        if len(v) > 50:
            raise ValueError('用户名长度不能超过50位')
        return v.strip()

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    username: str

    model_config = {"from_attributes": True}

@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(request: Request, user: UserCreate, db: AsyncSession = Depends(get_db)):
    # 检查用户名是否已存在
    stmt = select(User).where(User.username == user.username)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    # 生成 JWT 用于自动登录
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    # 查询用户
    stmt = select(User).where(User.username == user_credentials.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    # 验证密码
    if not user or not verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 生成 JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
