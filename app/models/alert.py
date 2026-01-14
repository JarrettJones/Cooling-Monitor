from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database import Base


class Alert(Base):
    """Alert/Alarm records for heat exchangers"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    heat_exchanger_id = Column(Integer, ForeignKey("heat_exchangers.id"), nullable=False)
    
    # Alert details
    type = Column(String, nullable=False)  # "CRITICAL_LOW_FLOW", "FAN_FAULT", etc.
    severity = Column(String, nullable=False, default="critical")  # "critical", "warning", "info"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Pump/device specific
    pump_id = Column(String, nullable=True)
    pump_name = Column(String, nullable=True)
    flow_rate = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    
    # Status tracking
    acknowledged = Column(Boolean, default=False)
    resolved = Column(Boolean, default=False)
    acknowledged_by = Column(String, nullable=True)  # Username
    resolved_by = Column(String, nullable=True)  # Username
    
    # Comments/notes
    comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relationship
    heat_exchanger = relationship("HeatExchanger", back_populates="alerts")


# Pydantic schemas
class AlertResponse(BaseModel):
    id: int
    heat_exchanger_id: int
    heat_exchanger_name: str | None = None
    type: str
    severity: str
    title: str
    description: str | None = None
    pump_id: str | None = None
    pump_name: str | None = None
    flow_rate: float | None = None
    threshold: float | None = None
    acknowledged: bool
    resolved: bool
    acknowledged_by: str | None = None
    resolved_by: str | None = None
    comments: str | None = None
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    
    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Schema for acknowledging an alert"""
    comments: str | None = None


class AlertResolve(BaseModel):
    """Schema for resolving an alert"""
    comments: str | None = None


class AlertComment(BaseModel):
    """Schema for adding a comment to an alert"""
    comments: str
