from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from app.database import Base


class Program(Base):
    """Program model for categorizing heat exchangers"""
    __tablename__ = "programs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Pydantic schemas
class ProgramCreate(BaseModel):
    name: str


class ProgramResponse(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
