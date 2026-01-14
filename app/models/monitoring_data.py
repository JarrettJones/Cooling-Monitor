from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Literal
import json
from app.database import Base


class MonitoringData(Base):
    __tablename__ = "monitoring_data"
    
    id = Column(Integer, primary_key=True, index=True)
    heat_exchanger_id = Column(Integer, ForeignKey("heat_exchangers.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    temperature = Column(Float, nullable=False)
    fan_speed = Column(Integer, nullable=False)
    power_consumption = Column(Float, nullable=False)
    humidity = Column(Float, nullable=True)
    status = Column(String, default="normal")
    raw_data = Column(Text, nullable=True)
    
    # CDU Ambient readings
    ambient_temperature = Column(Float, nullable=True)
    ambient_humidity = Column(Float, nullable=True)
    
    # Relationship
    heat_exchanger = relationship("HeatExchanger", back_populates="monitoring_data")


# Pydantic schemas
class MonitoringDataCreate(BaseModel):
    heat_exchanger_id: int
    temperature: float
    fan_speed: int
    power_consumption: float
    humidity: float | None = None
    status: Literal["normal", "warning", "critical"] = "normal"
    raw_data: dict | None = None


class MonitoringDataResponse(BaseModel):
    id: int
    heat_exchanger_id: int
    timestamp: datetime
    temperature: float
    fan_speed: int
    power_consumption: float
    humidity: float | None
    status: str
    ambient_temperature: float | None = None
    ambient_humidity: float | None = None
    raw_data: str | None = None
    
    class Config:
        from_attributes = True


class MonitoringStats(BaseModel):
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    avg_fan_speed: float
    avg_power_consumption: float
    total_data_points: int
