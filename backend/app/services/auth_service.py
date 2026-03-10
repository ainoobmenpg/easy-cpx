# Authentication Service - JWT based authentication with password hashing
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import jwt
import bcrypt
from sqlalchemy.orm import Session
from app.models import User, UserRole
from app.services.structured_logging import StructuredLogger

logger = StructuredLogger("auth_service")

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "cpx-default-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXP_MIN = int(os.getenv("JWT_EXP_MIN", "15"))  # 15 minutes for access token
JWT_REFRESH_EXP_MIN = int(os.getenv("JWT_REFRESH_EXP_MIN", "10080"))  # 7 days for refresh token


class AuthService:
    """Service for handling authentication with JWT"""

    def __init__(self, db: Session):
        self.db = db

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False

    def create_access_token(self, user_id: int, username: str, role: str) -> str:
        """Create a short-lived access token"""
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXP_MIN)
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "exp": expire,
            "type": "access"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def create_refresh_token(self, user_id: int) -> str:
        """Create a long-lived refresh token"""
        expire = datetime.utcnow() + timedelta(minutes=JWT_REFRESH_EXP_MIN)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "type": "refresh"
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired", extra={"reason": "Signature has expired"})
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("token_invalid", extra={"reason": str(e)})
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        user = self.db.query(User).filter(User.username == username).first()

        if not user:
            logger.warning("login_failed", extra={"username": username, "reason": "User not found"})
            return None

        if not user.is_active:
            logger.warning("login_failed", extra={"username": username, "reason": "User is inactive"})
            return None

        if not self.verify_password(password, user.password_hash):
            logger.warning("login_failed", extra={"username": username, "reason": "Invalid password"})
            return None

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        logger.info("login_success", extra={"user_id": user.id, "username": username})

        return {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "access_token": self.create_access_token(user.id, user.username, user.role.value),
            "refresh_token": self.create_refresh_token(user.id)
        }

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Create new access token from refresh token"""
        payload = self.decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            return None

        user_id = int(payload.get("sub"))
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            return None

        return {
            "access_token": self.create_access_token(user.id, user.username, user.role.value),
            "token_type": "bearer"
        }

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, username: str, password: str, role: str = "observer") -> User:
        """Create a new user with hashed password"""
        password_hash = self.hash_password(password)
        user = User(
            username=username,
            password_hash=password_hash,
            role=UserRole[role.upper()]
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info("user_created", extra={"user_id": user.id, "username": username})
        return user


# FastAPI dependency for getting current user
def get_current_user(token: str, db: Session) -> Optional[User]:
    """FastAPI dependency to get current user from JWT token"""
    auth_service = AuthService(db)
    payload = auth_service.decode_token(token)

    if not payload:
        return None

    if payload.get("type") != "access":
        return None

    user_id = int(payload.get("sub"))
    return auth_service.get_user_by_id(user_id)


# Token extraction from Authorization header
def extract_token(authorization: Optional[str]) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
