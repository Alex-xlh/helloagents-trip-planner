from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

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

    model_config = {"from_attributes": True}

class TripHistoryDetailResponse(TripHistoryResponse):
    trip_data: dict

@router.post("", response_model=TripHistoryResponse)
async def save_trip(trip: TripHistoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    db_trip = TripHistory(
        user_id=current_user.id,
        destination=trip.destination,
        trip_data=trip.trip_data
    )
    db.add(db_trip)
    await db.commit()
    await db.refresh(db_trip)
    return db_trip

@router.get("", response_model=List[TripHistoryResponse])
async def list_trips(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(TripHistory).where(TripHistory.user_id == current_user.id).order_by(TripHistory.created_at.desc())
    result = await db.execute(stmt)
    trips = result.scalars().all()
    return trips

@router.get("/{trip_id}", response_model=TripHistoryDetailResponse)
async def get_trip(trip_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(TripHistory).where(TripHistory.id == trip_id, TripHistory.user_id == current_user.id)
    result = await db.execute(stmt)
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="历史行程未找到")
        
    return trip
