"""
Session Management Service for HNC Legal Questionnaire System
Handles user sessions, timeouts, concurrent session management, and access control
"""

import redis
import json
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
import os

from services.auth_service import UserRole

# Configure logging
logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    IDLE_TIMEOUT = "idle_timeout"
    FORCE_LOGOUT = "force_logout"


@dataclass
class SessionInfo:
    session_id: str
    user_id: str
    username: str
    role: UserRole
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    status: SessionStatus
    permissions: List[str]
    expires_at: datetime
    is_temporary: bool = False  # Flag for JWT-based temporary sessions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session info to dictionary for storage"""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for key in ['created_at', 'last_activity', 'expires_at']:
            if isinstance(data[key], datetime):
                data[key] = data[key].isoformat()
        # Convert enums to strings
        data['status'] = data['status'].value
        data['role'] = data['role'].value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        """Create session info from dictionary"""
        # Convert ISO strings back to datetime objects
        for key in ['created_at', 'last_activity', 'expires_at']:
            if isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        # Convert strings back to enums
        data['status'] = SessionStatus(data['status'])
        data['role'] = UserRole(data['role'])
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def is_idle_timeout(self, idle_timeout_minutes: int = 30) -> bool:
        """Check if session has idle timeout"""
        idle_limit = self.last_activity + timedelta(minutes=idle_timeout_minutes)
        return datetime.now(timezone.utc) > idle_limit
    
    def is_active(self) -> bool:
        """Check if session is active and valid"""
        return (
            self.status == SessionStatus.ACTIVE and
            not self.is_expired() and
            not self.is_idle_timeout()
        )


class SessionManager:
    """Manages user sessions with Redis backend"""
    
    def __init__(self, redis_client: redis.Redis = None):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        if redis_client:
            self.redis_client = redis_client
        else:
            # Create Redis client with proper connection pool and timeout settings
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=10,
                socket_keepalive=True,
                socket_keepalive_options={}
            )
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.active_sessions_prefix = "active_sessions:"
        
        # Session configuration
        self.session_timeout_hours = 8  # Default session timeout
        self.idle_timeout_minutes = 30  # Idle timeout
        self.max_concurrent_sessions = 3  # Max concurrent sessions per user
        self.cleanup_interval_minutes = 15  # Session cleanup interval
        
        # Test connection and handle gracefully
        try:
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection test failed: {e}. Session features may be limited.")
            # Don't fail initialization, just log the warning
        
    def create_session(self, user_id: str, username: str, role: UserRole, 
                      ip_address: str, user_agent: str, 
                      permissions: List[str] = None) -> SessionInfo:
        """Create a new user session"""
        
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.session_timeout_hours)
        
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            username=username,
            role=role,
            created_at=now,
            last_activity=now,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE,
            permissions=permissions or self._get_role_permissions(role),
            expires_at=expires_at
        )
        
        try:
            # Check and enforce concurrent session limits
            self._enforce_concurrent_session_limit(user_id, session_id)
            
            # Store session data
            self._store_session(session)
            
            # Track user sessions
            self._add_user_session(user_id, session_id)
            
            # Add to active sessions
            self._add_active_session(session_id)
            
            logger.info(f"Created session {session_id} for user {username}")
        except Exception as e:
            logger.error(f"Error during session creation for {username}: {e}")
            # Continue with session creation even if Redis operations fail
            # This ensures authentication doesn't completely break
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Retrieve session information"""
        
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.redis_client.get(session_key)
            
            if not session_data:
                return None
            
            try:
                data = json.loads(session_data)
                session = SessionInfo.from_dict(data)
                
                # Check if session is still valid
                if not session.is_active():
                    self._terminate_session(session_id, 
                        SessionStatus.EXPIRED if session.is_expired() 
                        else SessionStatus.IDLE_TIMEOUT)
                    return None
                
                return session
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Invalid session data for {session_id}: {e}")
                # Invalid session data, remove it
                try:
                    self.redis_client.delete(session_key)
                except Exception as delete_error:
                    logger.error(f"Failed to delete invalid session {session_id}: {delete_error}")
                return None
                
        except Exception as e:
            logger.error(f"Redis error when getting session {session_id}: {e}")
            # Return None on Redis errors instead of crashing
            return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity timestamp"""
        
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.last_activity = datetime.now(timezone.utc)
        self._store_session(session)
        return True
    
    def terminate_session(self, session_id: str, 
                         status: SessionStatus = SessionStatus.TERMINATED) -> bool:
        """Terminate a specific session"""
        return self._terminate_session(session_id, status)
    
    def terminate_user_sessions(self, user_id: str, 
                               exclude_session_id: str = None) -> int:
        """Terminate all sessions for a user, optionally excluding one session"""
        
        user_sessions = self._get_user_sessions(user_id)
        terminated_count = 0
        
        for session_id in user_sessions:
            if session_id != exclude_session_id:
                if self._terminate_session(session_id, SessionStatus.FORCE_LOGOUT):
                    terminated_count += 1
        
        return terminated_count
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user"""
        
        session_ids = self._get_user_sessions(user_id)
        sessions = []
        
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session and session.is_active():
                sessions.append(session)
        
        return sessions
    
    def validate_session_permission(self, session_id: str, 
                                  required_permission: str) -> bool:
        """Check if session has required permission"""
        
        session = self.get_session(session_id)
        if not session or not session.is_active():
            return False
        
        return required_permission in session.permissions
    
    def extend_session(self, session_id: str, 
                      extension_hours: int = None) -> bool:
        """Extend session expiration time"""
        
        session = self.get_session(session_id)
        if not session:
            return False
        
        extension = extension_hours or self.session_timeout_hours
        session.expires_at = datetime.now(timezone.utc) + timedelta(hours=extension)
        session.last_activity = datetime.now(timezone.utc)
        
        self._store_session(session)
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired and invalid sessions"""
        
        active_sessions = self._get_all_active_sessions()
        cleaned_count = 0
        
        for session_id in active_sessions:
            session = self.get_session(session_id)
            if not session or not session.is_active():
                self._terminate_session(session_id, SessionStatus.EXPIRED)
                cleaned_count += 1
        
        return cleaned_count
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        
        active_sessions = self._get_all_active_sessions()
        user_session_counts = {}
        role_counts = {}
        
        for session_id in active_sessions:
            session = self.get_session(session_id)
            if session and session.is_active():
                # Count by user
                user_session_counts[session.user_id] = user_session_counts.get(session.user_id, 0) + 1
                
                # Count by role
                role_counts[session.role.value] = role_counts.get(session.role.value, 0) + 1
        
        return {
            "total_active_sessions": len(active_sessions),
            "unique_users": len(user_session_counts),
            "sessions_by_role": role_counts,
            "average_sessions_per_user": len(active_sessions) / len(user_session_counts) if user_session_counts else 0,
            "users_with_multiple_sessions": len([count for count in user_session_counts.values() if count > 1])
        }
    
    def _store_session(self, session: SessionInfo):
        """Store session data in Redis"""
        try:
            session_key = f"{self.session_prefix}{session.session_id}"
            session_data = json.dumps(session.to_dict())
            
            # Set with expiration
            expiration_seconds = int((session.expires_at - datetime.now(timezone.utc)).total_seconds())
            if expiration_seconds > 0:
                self.redis_client.setex(session_key, expiration_seconds, session_data)
        except Exception as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")
            # Don't raise the exception, just log it
    
    def _terminate_session(self, session_id: str, status: SessionStatus) -> bool:
        """Internal method to terminate a session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Update session status
            session.status = status
            self._store_session(session)
            
            # Remove from active sessions and user sessions
            self._remove_active_session(session_id)
            self._remove_user_session(session.user_id, session_id)
            
            # Delete session data after a grace period (for audit logs)
            grace_period_seconds = 3600  # 1 hour
            session_key = f"{self.session_prefix}{session_id}"
            try:
                self.redis_client.expire(session_key, grace_period_seconds)
            except Exception as e:
                logger.error(f"Failed to set expiration on terminated session {session_id}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to terminate session {session_id}: {e}")
            return False
    
    def _enforce_concurrent_session_limit(self, user_id: str, new_session_id: str):
        """Enforce maximum concurrent sessions per user"""
        try:
            user_sessions = self._get_user_sessions(user_id)
            
            # If we're at the limit, terminate the oldest session
            if len(user_sessions) >= self.max_concurrent_sessions:
                sessions_to_check = []
                
                for session_id in user_sessions:
                    session = self.get_session(session_id)
                    if session and session.is_active():
                        sessions_to_check.append(session)
                
                # Sort by creation time and terminate oldest
                sessions_to_check.sort(key=lambda s: s.created_at)
                sessions_to_terminate = sessions_to_check[:len(sessions_to_check) - self.max_concurrent_sessions + 1]
                
                for session in sessions_to_terminate:
                    self._terminate_session(session.session_id, SessionStatus.FORCE_LOGOUT)
        except Exception as e:
            logger.error(f"Failed to enforce concurrent session limit for {user_id}: {e}")
    
    def _get_user_sessions(self, user_id: str) -> Set[str]:
        """Get session IDs for a user"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = self.redis_client.smembers(user_sessions_key)
            return {session_id.decode() if isinstance(session_id, bytes) else session_id for session_id in session_ids}
        except Exception as e:
            logger.error(f"Failed to get user sessions for {user_id}: {e}")
            return set()
    
    def _add_user_session(self, user_id: str, session_id: str):
        """Add session to user's session list"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            self.redis_client.sadd(user_sessions_key, session_id)
            # Set expiration on user sessions key
            self.redis_client.expire(user_sessions_key, 86400 * 7)  # 7 days
        except Exception as e:
            logger.error(f"Failed to add user session for {user_id}: {e}")
    
    def _remove_user_session(self, user_id: str, session_id: str):
        """Remove session from user's session list"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            self.redis_client.srem(user_sessions_key, session_id)
        except Exception as e:
            logger.error(f"Failed to remove user session for {user_id}: {e}")
    
    def _get_all_active_sessions(self) -> Set[str]:
        """Get all active session IDs"""
        try:
            active_sessions_key = f"{self.active_sessions_prefix}all"
            session_ids = self.redis_client.smembers(active_sessions_key)
            return {session_id.decode() if isinstance(session_id, bytes) else session_id for session_id in session_ids}
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")
            return set()
    
    def _add_active_session(self, session_id: str):
        """Add session to active sessions list"""
        try:
            active_sessions_key = f"{self.active_sessions_prefix}all"
            self.redis_client.sadd(active_sessions_key, session_id)
        except Exception as e:
            logger.error(f"Failed to add active session {session_id}: {e}")
    
    def _remove_active_session(self, session_id: str):
        """Remove session from active sessions list"""
        try:
            active_sessions_key = f"{self.active_sessions_prefix}all"
            self.redis_client.srem(active_sessions_key, session_id)
        except Exception as e:
            logger.error(f"Failed to remove active session {session_id}: {e}")
    
    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """Get default permissions for a role"""
        
        permissions_map = {
            UserRole.ADMIN: [
                "read_all_clients",
                "write_all_clients",
                "delete_clients",
                "manage_users",
                "view_reports",
                "export_data",
                "system_admin",
                "audit_logs"
            ],
            UserRole.LAWYER: [
                "read_own_clients",
                "write_own_clients",
                "read_shared_clients",
                "view_reports",
                "export_data",
                "ai_proposals"
            ],
            UserRole.ASSISTANT: [
                "read_shared_clients",
                "write_shared_clients",
                "basic_reports"
            ]
        }
        
        return permissions_map.get(role, [])


# Global session manager instance
session_manager = SessionManager()


class AccessControl:
    """Access control utilities for checking permissions"""
    
    @staticmethod
    def require_permission(permission: str):
        """Decorator to require specific permission for endpoint access"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # This would be used with FastAPI dependency injection
                # Implementation depends on how session_id is passed to endpoints
                pass
            return wrapper
        return decorator
    
    @staticmethod
    def check_client_access(session: SessionInfo, client_id: str, 
                          action: str = "read") -> bool:
        """Check if user has access to specific client data"""
        
        if session.role == UserRole.ADMIN:
            return True
        
        if action == "read":
            return (
                "read_all_clients" in session.permissions or
                "read_own_clients" in session.permissions or
                "read_shared_clients" in session.permissions
            )
        elif action == "write":
            return (
                "write_all_clients" in session.permissions or
                "write_own_clients" in session.permissions or
                "write_shared_clients" in session.permissions
            )
        elif action == "delete":
            return "delete_clients" in session.permissions
        
        return False
    
    @staticmethod
    def filter_accessible_clients(session: SessionInfo, 
                                 all_clients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter client list based on user permissions"""
        
        if session.role == UserRole.ADMIN or "read_all_clients" in session.permissions:
            return all_clients
        
        # For now, return all (implement client ownership logic as needed)
        return all_clients