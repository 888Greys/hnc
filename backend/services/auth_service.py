"""
Authentication Service for HNC Legal Questionnaire System
Provides comprehensive user authentication, session management, and security features
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
from enum import Enum

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

# Configure logging
logger = logging.getLogger(__name__)

# User roles enum
class UserRole(Enum):
    ADMIN = "admin"
    LAWYER = "lawyer"
    ASSISTANT = "assistant"

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# User models
class User(BaseModel):
    id: str
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    role: str = Field(default="lawyer", pattern="^(admin|lawyer|assistant)$")
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="lawyer", pattern="^(admin|lawyer|assistant)$")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class PasswordReset(BaseModel):
    reset_token: str
    new_password: str = Field(..., min_length=8)

class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserSession(BaseModel):
    session_id: str
    user_id: str
    username: str
    role: str
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AuthenticationService:
    """Comprehensive authentication service"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.users_dir = self.data_dir / "users"
        self.sessions_dir = self.data_dir / "sessions"
        self.tokens_dir = self.data_dir / "tokens"
        
        # Create directories
        for directory in [self.users_dir, self.sessions_dir, self.tokens_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize default admin user
        self._ensure_admin_user()
    
    def _ensure_admin_user(self):
        """Ensure default admin user exists"""
        try:
            admin_file = self.users_dir / "admin.json"
            if not admin_file.exists():
                admin_user = {
                    "id": "admin",
                    "username": "admin",
                    "email": "admin@hnc-legal.com",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": "admin",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "password_hash": self.hash_password("admin123"),
                    "failed_login_attempts": 0,
                    "locked_until": None
                }
                
                with open(admin_file, 'w') as f:
                    json.dump(admin_user, f, indent=2)
                
                logger.info("Default admin user created")
        except Exception as e:
            logger.error(f"Failed to create admin user: {e}")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> List[str]:
        """Validate password strength and return list of issues"""
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            issues.append("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Password must contain at least one special character")
        
        # Check for common passwords
        common_passwords = ["password", "123456", "admin", "user", "test"]
        if password.lower() in common_passwords:
            issues.append("Password is too common")
        
        return issues
    
    def generate_user_id(self) -> str:
        """Generate unique user ID"""
        return f"user_{secrets.token_hex(8)}"
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        try:
            # Check if username exists
            if self.get_user_by_username(user_data.username):
                raise HTTPException(
                    status_code=400,
                    detail="Username already exists"
                )
            
            # Check if email exists
            if self.get_user_by_email(user_data.email):
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )
            
            # Validate password strength
            password_issues = self.validate_password_strength(user_data.password)
            if password_issues:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password validation failed: {', '.join(password_issues)}"
                )
            
            # Create user
            user_id = self.generate_user_id()
            now = datetime.now(timezone.utc)
            
            user_dict = {
                "id": user_id,
                "username": user_data.username,
                "email": user_data.email,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "role": user_data.role,
                "is_active": True,
                "created_at": now.isoformat(),
                "password_hash": self.hash_password(user_data.password),
                "password_changed_at": now.isoformat(),
                "failed_login_attempts": 0,
                "locked_until": None
            }
            
            # Save user
            user_file = self.users_dir / f"{user_data.username}.json"
            with open(user_file, 'w') as f:
                json.dump(user_dict, f, indent=2)
            
            # Return user object (without password hash)
            user_dict.pop("password_hash")
            user_dict["created_at"] = now
            
            logger.info(f"User created: {user_data.username}")
            return User(**user_dict)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create user"
            )
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            user_file = self.users_dir / f"{username}.json"
            if user_file.exists():
                with open(user_file, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading user {username}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            for user_file in self.users_dir.glob("*.json"):
                with open(user_file, 'r') as f:
                    user_data = json.load(f)
                    if user_data.get("email") == email:
                        return user_data
            return None
        except Exception as e:
            logger.error(f"Error searching user by email {email}: {e}")
            return None
    
    def update_user(self, username: str, updates: UserUpdate) -> User:
        """Update user information"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Update fields
            update_dict = updates.dict(exclude_unset=True)
            for field, value in update_dict.items():
                if field == "email" and value != user_data.get("email"):
                    # Check if new email already exists
                    if self.get_user_by_email(value):
                        raise HTTPException(
                            status_code=400,
                            detail="Email already exists"
                        )
                user_data[field] = value
            
            # Save updated user
            user_file = self.users_dir / f"{username}.json"
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            # Return user object (without password hash)
            user_data.pop("password_hash", None)
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
            
            logger.info(f"User updated: {username}")
            return User(**user_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user {username}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to update user"
            )
    
    def change_password(self, username: str, password_change: PasswordChange) -> bool:
        """Change user password"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )
            
            # Verify current password
            if not self.verify_password(password_change.current_password, user_data["password_hash"]):
                raise HTTPException(
                    status_code=400,
                    detail="Current password is incorrect"
                )
            
            # Validate new password strength
            password_issues = self.validate_password_strength(password_change.new_password)
            if password_issues:
                raise HTTPException(
                    status_code=400,
                    detail=f"Password validation failed: {', '.join(password_issues)}"
                )
            
            # Update password
            user_data["password_hash"] = self.hash_password(password_change.new_password)
            user_data["password_changed_at"] = datetime.now(timezone.utc).isoformat()
            
            # Save user
            user_file = self.users_dir / f"{username}.json"
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            logger.info(f"Password changed for user: {username}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error changing password for {username}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to change password"
            )
    
    def is_user_locked(self, username: str) -> bool:
        """Check if user account is locked"""
        user_data = self.get_user_by_username(username)
        if not user_data:
            return False
        
        locked_until = user_data.get("locked_until")
        if locked_until:
            locked_time = datetime.fromisoformat(locked_until)
            if datetime.now(timezone.utc) < locked_time:
                return True
            else:
                # Lock has expired, reset failed attempts
                self._reset_failed_attempts(username)
        
        return False
    
    def _reset_failed_attempts(self, username: str):
        """Reset failed login attempts"""
        try:
            user_data = self.get_user_by_username(username)
            if user_data:
                user_data["failed_login_attempts"] = 0
                user_data["locked_until"] = None
                
                user_file = self.users_dir / f"{username}.json"
                with open(user_file, 'w') as f:
                    json.dump(user_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error resetting failed attempts for {username}: {e}")
    
    def _increment_failed_attempts(self, username: str):
        """Increment failed login attempts and lock account if necessary"""
        try:
            user_data = self.get_user_by_username(username)
            if not user_data:
                return
            
            user_data["failed_login_attempts"] = user_data.get("failed_login_attempts", 0) + 1
            
            # Lock account if max attempts exceeded
            if user_data["failed_login_attempts"] >= MAX_LOGIN_ATTEMPTS:
                lockout_time = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                user_data["locked_until"] = lockout_time.isoformat()
                logger.warning(f"Account locked for user: {username}")
            
            user_file = self.users_dir / f"{username}.json"
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error incrementing failed attempts for {username}: {e}")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        try:
            # Check if user exists
            user_data = self.get_user_by_username(username)
            if not user_data:
                return None
            
            # Check if account is active
            if not user_data.get("is_active", True):
                raise HTTPException(
                    status_code=403,
                    detail="Account is disabled"
                )
            
            # Check if account is locked
            if self.is_user_locked(username):
                raise HTTPException(
                    status_code=423,
                    detail="Account is temporarily locked due to too many failed login attempts"
                )
            
            # Verify password
            if not self.verify_password(password, user_data["password_hash"]):
                self._increment_failed_attempts(username)
                return None
            
            # Reset failed attempts on successful login
            self._reset_failed_attempts(username)
            
            # Update last login time
            user_data["last_login"] = datetime.now(timezone.utc).isoformat()
            user_file = self.users_dir / f"{username}.json"
            with open(user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            
            # Remove password hash from returned data
            user_data.pop("password_hash")
            return user_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
                return None
            
            return payload
            
        except JWTError:
            return None
    
    def create_session(self, user_data: Dict[str, Any], ip_address: str = None, user_agent: str = None) -> UserSession:
        """Create user session"""
        try:
            session_id = secrets.token_hex(32)
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(hours=8)  # 8-hour session
            
            session = UserSession(
                session_id=session_id,
                user_id=user_data["id"],
                username=user_data["username"],
                role=user_data["role"],
                created_at=now,
                last_accessed=now,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Save session
            session_file = self.sessions_dir / f"{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(session.dict(), f, indent=2, default=str)
            
            logger.info(f"Session created for user: {user_data['username']}")
            return session
            
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to create session"
            )
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get user session"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                session = UserSession(**session_data)
                
                # Check if session is expired
                if session.expires_at < datetime.now(timezone.utc):
                    self.delete_session(session_id)
                    return None
                
                # Update last accessed time
                session.last_accessed = datetime.now(timezone.utc)
                with open(session_file, 'w') as f:
                    json.dump(session.dict(), f, indent=2, default=str)
                
                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete user session"""
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Session deleted: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            now = datetime.now(timezone.utc)
            expired_count = 0
            
            for session_file in self.sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r') as f:
                        session_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(session_data["expires_at"])
                    if expires_at < now:
                        session_file.unlink()
                        expired_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing session file {session_file}: {e}")
            
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")

# Global authentication service instance
auth_service = AuthenticationService(data_dir=os.getenv("DATA_DIR", "data"))

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    try:
        # Verify token
        payload = auth_service.verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user data
        user_data = auth_service.get_user_by_username(username)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user_data.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )
        
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user with admin role verification"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user