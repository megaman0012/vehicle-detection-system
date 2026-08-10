"""
Security utilities for Vehicle Detection System
Handles password hashing, JWT tokens, role-based access control, and audit logging
"""
from datetime import datetime, timedelta
from typing import Optional, Union, Any, Dict, List
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Role definitions
ROLES = {
    "admin": ["read", "write", "delete", "admin"],
    "operator": ["read", "write"],
    "user": ["read"]
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Refresh tokens typically last longer than access tokens
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Get current authenticated user"""
    payload = verify_token(token)
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Get current admin user"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def check_permission(user: User, permission: str) -> bool:
    """Check if user has a specific permission"""
    user_permissions = ROLES.get(user.role, [])
    return permission in user_permissions

def require_permission(permission: str):
    """Dependency to check for specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} required"
            )
        return current_user
    return permission_checker

# Audit logging
import logging
from models.audit import AuditLog

logger = logging.getLogger("audit")

def log_audit_event(
    db: Session,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: str,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Log an audit event"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        logger.info(f"Audit log recorded: {user_id} performed {action} on {resource_type}")
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        db.rollback()

# Rate limiting
import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, key: str) -> bool:
        """Check if a request is allowed based on rate limit"""
        now = time.time()
        with self.lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < self.window_seconds
            ]
            
            # Check if under limit
            if len(self.requests[key]) < self.max_requests:
                self.requests[key].append(now)
                return True
            else:
                return False

# Global rate limiters
auth_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)  # 5 attempts per minute
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 requests per minute

def check_auth_rate_limit(ip_address: str) -> bool:
    """Check authentication rate limit"""
    return auth_rate_limiter.is_allowed(f"auth:{ip_address}")

def check_api_rate_limit(ip_address: str) -> bool:
    """Check API rate limit"""
    return api_rate_limiter.is_allowed(f"api:{ip_address}")