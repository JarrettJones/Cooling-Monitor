from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database import Base


class HeatExchanger(Base):
    __tablename__ = "heat_exchangers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    type = Column(String, nullable=True)  # Callan or Atlas
    rscm_ip = Column(String, unique=True, nullable=False)
    city = Column(String, nullable=False)
    building = Column(String, nullable=False)
    room = Column(String, nullable=False)
    tile = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    program_id = Column(Integer, ForeignKey('programs.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # R-SCM Manager Information
    manager_type = Column(String, nullable=True)
    model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    status_state = Column(String, nullable=True)
    status_health = Column(String, nullable=True)
    hostname = Column(String, nullable=True)
    unique_id = Column(String, nullable=True)
    time_since_boot = Column(String, nullable=True)
    
    # CDU Controller Status (store as JSON for complex nested data)
    cdu_controller_status = Column(String, nullable=True)  # JSON string
    cdu_chassis_status = Column(String, nullable=True)  # JSON string for Status.State and Status.Health
    cdu_alarms = Column(String, nullable=True)  # JSON string for all alarm data
    fan_status = Column(String, nullable=True)  # JSON string for fan status array
    pump_status = Column(String, nullable=True)  # JSON string for pump status array
    urgent_alarms = Column(String, nullable=True)  # JSON string for urgent alarms
    
    # Relationships
    monitoring_data = relationship("MonitoringData", back_populates="heat_exchanger", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="heat_exchanger", cascade="all, delete-orphan")
    program = relationship("Program")

# Pydantic schemas for API
class Location(BaseModel):
    city: str
    building: str
    room: str
    tile: str


class HeatExchangerBase(BaseModel):
    name: str
    type: str | None = None  # Callan or Atlas
    rscm_ip: str
    location: Location
    is_active: bool = True
    program_id: Optional[int] = None


class HeatExchangerCreate(HeatExchangerBase):
    pass


class HeatExchangerUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    rscm_ip: str | None = None
    location: Location | None = None
    is_active: bool | None = None
    program_id: Optional[int] = None


class HeatExchangerResponse(BaseModel):
    id: int
    type: str | None = None
    name: str
    rscm_ip: str
    location: Location
    is_active: bool
    program_id: Optional[int] = None
    program_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Manager information
    manager_type: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    status_state: str | None = None
    status_health: str | None = None
    hostname: str | None = None
    unique_id: str | None = None
    time_since_boot: str | None = None
    
    # CDU Controller Status
    cdu_controller_status: str | None = None
    cdu_chassis_status: str | None = None
    cdu_alarms: str | None = None
    fan_status: str | None = None
    pump_status: str | None = None
    urgent_alarms: str | None = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_model(cls, db_model: HeatExchanger):
        return cls(
            id=db_model.id,
            type=db_model.type,
            name=db_model.name,
            rscm_ip=db_model.rscm_ip,
            location=Location(
                city=db_model.city,
                building=db_model.building,
                room=db_model.room,
                tile=db_model.tile
            ),
            is_active=db_model.is_active,
            program_id=db_model.program_id,
            program_name=db_model.program.name if db_model.program else None,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            manager_type=db_model.manager_type,
            model=db_model.model,
            firmware_version=db_model.firmware_version,
            status_state=db_model.status_state,
            status_health=db_model.status_health,
            hostname=db_model.hostname,
            unique_id=db_model.unique_id,
            time_since_boot=db_model.time_since_boot,
            cdu_controller_status=db_model.cdu_controller_status,
            cdu_chassis_status=db_model.cdu_chassis_status,
            cdu_alarms=db_model.cdu_alarms,
            fan_status=db_model.fan_status,
            pump_status=db_model.pump_status,
            urgent_alarms=db_model.urgent_alarms
        )
