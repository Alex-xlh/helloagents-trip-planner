from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from pydantic import BaseModel, field_validator
from datetime import datetime, timezone
import hashlib
import json

from ...core.database import get_db
from ...core.auth import get_current_user
from ...models.db import User, TripHistory

router = APIRouter(prefix="/history", tags=["history"])

class TripHistoryCreate(BaseModel):
    destination: str
    trip_data: dict

class TripHistoryResponse(BaseModel):
    id: int
    destination: str
    created_at: datetime
    travel_days: int = 0
    total_budget: int = 0
    thumbnail: str = ""

    model_config = {"from_attributes": True}

class PaginatedTripResponse(BaseModel):
    items: List[TripHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

class TripHistoryDetailResponse(TripHistoryResponse):
    trip_data: dict

@router.post("", response_model=TripHistoryResponse)
async def save_trip(trip: TripHistoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # 计算 trip_data 的 hash
    trip_json = json.dumps(trip.trip_data, sort_keys=True, ensure_ascii=False)
    trip_hash = hashlib.md5(trip_json.encode('utf-8')).hexdigest()

    # 检查是否已存在完全相同的行程
    stmt = select(TripHistory).where(
        TripHistory.user_id == current_user.id,
        TripHistory.destination == trip.destination,
        TripHistory.trip_hash == trip_hash
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()

    if existing:
        # 更新 created_at 为最新
        existing.created_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(existing)
        return existing

    db_trip = TripHistory(
        user_id=current_user.id,
        destination=trip.destination,
        trip_data=trip.trip_data,
        trip_hash=trip_hash
    )
    db.add(db_trip)
    await db.commit()
    await db.refresh(db_trip)
    return db_trip

@router.get("", response_model=PaginatedTripResponse)
async def list_trips(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    # 查询总数
    count_stmt = select(func.count()).select_from(TripHistory).where(TripHistory.user_id == current_user.id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    # 查询当前页
    stmt = (
        select(TripHistory)
        .where(TripHistory.user_id == current_user.id)
        .order_by(TripHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    trips = result.scalars().all()

    items = []
    for t in trips:
        trip_data = t.trip_data or {}
        items.append(TripHistoryResponse(
            id=t.id,
            destination=t.destination,
            created_at=t.created_at,
            travel_days=len(trip_data.get('days', [])),
            total_budget=trip_data.get('budget', {}).get('total', 0) if trip_data.get('budget') else 0,
            thumbnail=trip_data.get('days', [{}])[0].get('attractions', [{}])[0].get('image_url', '') if trip_data.get('days') and trip_data.get('days')[0].get('attractions') else ''
        ))

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size)
    }

@router.get("/{trip_id}", response_model=TripHistoryDetailResponse)
async def get_trip(trip_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(TripHistory).where(TripHistory.id == trip_id, TripHistory.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="历史行程未找到")
        
    return trip

@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除当前用户的指定行程"""
    stmt = select(TripHistory).where(
        TripHistory.id == trip_id,
        TripHistory.user_id == current_user.id
    )
    result = await db.execute(stmt)
    trip = result.scalars().first()

    if not trip:
        raise HTTPException(status_code=404, detail="历史行程未找到")

    await db.delete(trip)
    await db.commit()
    return {"message": "已删除", "id": trip_id}
