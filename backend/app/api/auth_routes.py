# Authentication API Routes
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app.services.auth_service import AuthService, extract_token
from app.models import User
import jwt
import os

router = APIRouter()

JWT_SECRET = os.getenv("JWT_SECRET", "cpx-default-secret-change-in-production")
JWT_ALGORITHM = "HS256"


# Request/Response models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = Field(default="observer", pattern="^(blue|red|white|observer|admin)$")


class UserResponse(BaseModel):
    user_id: int
    username: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


# Authentication endpoints
@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT tokens"""
    auth_service = AuthService(db)
    result = auth_service.authenticate_user(request.username, request.password)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return TokenResponse(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer"
    )


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    auth_service = AuthService(db)
    result = auth_service.refresh_access_token(request.refresh_token)

    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    return TokenResponse(
        access_token=result["access_token"],
        token_type="bearer"
    )


@router.post("/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    """Logout user (client should discard tokens)"""
    # In a stateless JWT system, logout is handled client-side
    # For refresh token invalidation, a blacklist could be implemented
    return {"message": "Logged out successfully"}


@router.get("/auth/me", response_model=UserResponse)
def get_current_user_info(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    token = extract_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    auth_service = AuthService(db)
    payload = auth_service.decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = int(payload.get("sub"))
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )


@router.post("/auth/register", response_model=UserResponse)
def register(request: UserCreateRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    auth_service = AuthService(db)

    # Check if username already exists
    existing = db.query(User).filter(User.username == request.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = auth_service.create_user(request.username, request.password, request.role)

    return UserResponse(
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )
