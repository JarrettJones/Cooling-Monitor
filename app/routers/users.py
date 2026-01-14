from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel, Field
from typing import List, Optional

from app.database import get_session
from app.models.user import User, UserResponse
from app.routers.auth import require_admin, get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    """Schema for creating a new user"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(admin|technician)$")


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    password: Optional[str] = Field(None, min_length=6)
    role: Optional[str] = Field(None, pattern="^(admin|technician)$")


class UserResponseExtended(BaseModel):
    """Extended user response with role name"""
    id: int
    username: str
    role: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[UserResponseExtended])
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """List all users (admin only)"""
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()
    
    return [
        UserResponseExtended(
            id=user.id,
            username=user.username,
            role="admin" if user.is_admin else "technician",
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
        for user in users
    ]


@router.post("/", response_model=UserResponseExtended, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """Create a new user (admin only)"""
    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == user_data.username)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create new user
    is_admin = 1 if user_data.role == "admin" else 0
    new_user = User(
        username=user_data.username,
        hashed_password=User.hash_password(user_data.password),
        is_admin=is_admin
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return UserResponseExtended(
        id=new_user.id,
        username=new_user.username,
        role=user_data.role,
        created_at=new_user.created_at.isoformat() if new_user.created_at else ""
    )


@router.put("/{user_id}", response_model=UserResponseExtended)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """Update a user (admin only)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Don't allow changing your own role or deleting yourself
    if user.id == current_user.id and user_data.role and user_data.role == "technician":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot demote yourself from admin"
        )
    
    # Update password if provided
    if user_data.password:
        user.hashed_password = User.hash_password(user_data.password)
    
    # Update role if provided
    if user_data.role:
        user.is_admin = 1 if user_data.role == "admin" else 0
    
    await db.commit()
    await db.refresh(user)
    
    return UserResponseExtended(
        id=user.id,
        username=user.username,
        role="admin" if user.is_admin else "technician",
        created_at=user.created_at.isoformat() if user.created_at else ""
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_session)
):
    """Delete a user (admin only)"""
    # Don't allow deleting yourself
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    
    return {"message": f"User {user.username} deleted successfully"}
