from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trips = relationship("TripHistory", back_populates="user", cascade="all, delete-orphan")

class TripHistory(Base):
    __tablename__ = "trip_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination = Column(String(100), nullable=False)
    trip_data = Column(JSON, nullable=False) # 保存生成的完整旅行计划 JSON
    trip_hash = Column(String(64), nullable=True) # MD5 hash of trip_data JSON
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="trips")
