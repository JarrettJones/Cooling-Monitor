from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
from app.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    team = Column(String, nullable=True)
    business_justification = Column(String, nullable=True)
    is_admin = Column(Integer, default=0)  # SQLite uses 1/0 for boolean
    is_active = Column(Integer, default=0)  # New users require approval
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.hashed_password.encode('utf-8'))
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')


class LoginRequest(BaseModel):
    """Schema for login request"""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: Optional[str] = None
    team: Optional[str] = None
    is_admin: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    """Schema for user registration"""
    email: str
    username: str
    password: str
    confirm_password: str
    first_name: str
    last_name: Optional[str] = None
    team: Optional[str] = None
    business_justification: str
