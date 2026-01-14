from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
from app.database import Base


class SystemSettings(Base):
    """System-wide settings stored in database"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    redfish_username = Column(String, nullable=False, default="admin")
    redfish_password = Column(String, nullable=False, default="admin")
    
    # Email/SMTP settings (encrypted)
    smtp_enabled = Column(Boolean, default=False)
    smtp_server = Column(String, default="smtp.office365.com")
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String, default="")
    smtp_password = Column(String, default="")  # Encrypted
    smtp_from_email = Column(String, default="")
    smtp_to_emails = Column(String, default="")  # JSON array as string
    smtp_use_tls = Column(Boolean, default=True)
    
    # Microsoft Teams webhook settings
    teams_enabled = Column(Boolean, default=False)
    teams_webhook_url = Column(String, default="")  # Incoming webhook URL
    
    # Alarm thresholds
    pump_flow_critical_threshold = Column(Float, default=10.0)
    
    # Monitoring control
    monitoring_enabled = Column(Boolean, default=True)
    polling_interval_seconds = Column(Integer, default=30)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RedfishCredentialsUpdate(BaseModel):
    """Schema for updating Redfish credentials"""
    username: str
    password: str


class SMTPSettingsUpdate(BaseModel):
    """Schema for updating SMTP email and Teams notification settings"""
    smtp_enabled: bool = False
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""  # Will be encrypted before storage
    smtp_from_email: str = ""
    smtp_to_emails: List[str] = Field(default_factory=list)
    smtp_use_tls: bool = True
    teams_enabled: bool = False
    teams_webhook_url: str = ""
    pump_flow_critical_threshold: float = 10.0


class RedfishCredentialsResponse(BaseModel):
    """Schema for Redfish credentials response (without password)"""
    username: str
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True


class SMTPSettingsResponse(BaseModel):
    """Schema for SMTP and Teams notification settings response (without password)"""
    smtp_enabled: bool
    smtp_server: str
    smtp_port: int
    smtp_username: str
    smtp_from_email: str
    smtp_to_emails: List[str]
    smtp_use_tls: bool
    teams_enabled: bool
    teams_webhook_url: str
    pump_flow_critical_threshold: float
    updated_at: datetime | None = None
    
    class Config:
        from_attributes = True
