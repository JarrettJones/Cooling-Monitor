from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets

from app.database import get_session
from app.models.user import User, LoginRequest, UserResponse
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Use secret key from settings for JWT tokens
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(request: Request, db: AsyncSession = Depends(get_session)) -> User:
    """Dependency to get current authenticated user from cookie"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    try:
        print(f"[DEBUG AUTH] Attempting to decode token with SECRET_KEY length: {len(SECRET_KEY)}")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[DEBUG AUTH] Token decoded successfully, payload: {payload}")
        user_id_str: str = payload.get("sub")
        print(f"[DEBUG AUTH] Extracted user_id string: {user_id_str}")
        if user_id_str is None:
            print("[DEBUG AUTH] user_id is None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        user_id = int(user_id_str)
        print(f"[DEBUG AUTH] Converted to user_id int: {user_id}")
    except JWTError as e:
        print(f"[DEBUG AUTH] JWTError during token decode: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        print(f"[DEBUG AUTH] User with id {user_id} not found in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    print(f"[DEBUG AUTH] User authenticated successfully: {user.username}")
    return user


async def get_current_user_optional(request: Request) -> User | None:
    """Get current user from JWT token in cookie, return None if not authenticated"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            return None
        user_id = int(user_id_str)
        
        from app.database import get_session
        async for db in get_session():
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            return user
    except:
        return None


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.post("/login")
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session)
):
    """Login endpoint"""
    result = await db.execute(
        select(User).where(User.username == login_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    print(f"[DEBUG AUTH] Creating token for user_id: {user.id}, username: {user.username}")
    print(f"[DEBUG AUTH] Using SECRET_KEY length: {len(SECRET_KEY)}")
    access_token = create_access_token(data={"sub": str(user.id)})
    print(f"[DEBUG AUTH] Token created: {access_token[:50]}...")
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        samesite="lax"
    )
    print("[DEBUG AUTH] Cookie set successfully")
    
    return {
        "message": "Login successful",
        "user": UserResponse.model_validate(user)
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout endpoint"""
    response.delete_cookie("access_token")
    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse.model_validate(current_user)
