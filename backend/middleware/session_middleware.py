"""
Session Middleware for HNC Legal Questionnaire System
Handles session validation, access control, and automatic session updates
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import logging

from services.session_service import session_manager, SessionInfo, SessionStatus, AccessControl
from services.auth_service import auth_service, UserRole


logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware to handle session validation and management"""
    
    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/auth/login",
            "/auth/register",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next):
        """Process request and validate session if required"""
        
        logger.info(f"Session middleware ENTRY: {request.method} {request.url.path}")
        
        # Skip session validation for excluded paths
        if request.url.path == "/" or any(request.url.path.startswith(path) for path in self.excluded_paths if path != "/"):
            logger.info(f"Path {request.url.path} is excluded, skipping middleware")
            return await call_next(request)
        
        logger.info(f"Processing authentication for: {request.url.path}")
        
        # Extract session token from request
        session_id = self._extract_session_token(request)
        
        logger.info(f"Session middleware processing {request.url.path}, extracted token: {'[JWT TOKEN]' if session_id else 'None'}")
        
        if not session_id:
            logger.warning(f"No session token found for {request.url.path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Session token required"}
            )
        
        logger.info(f"Attempting to validate session/JWT token for: {request.url.path}")
        
        # Validate session - try session ID first, then JWT token
        session = session_manager.get_session(session_id)
        
        if not session or not session.is_active():
            logger.info(f"No active session found for token, trying JWT validation...")
            # If no valid session found, try to validate as JWT token
            jwt_payload = auth_service.verify_token(session_id)
            if not jwt_payload:
                logger.warning(f"JWT token validation failed for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired session"}
                )
            
            logger.info(f"JWT token validated successfully for user {jwt_payload.get('sub')}")
            
            # Create a temporary session info from JWT token for this request
            username = jwt_payload.get("sub")
            role_str = jwt_payload.get("role")
            
            if not username or not role_str:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token payload"}
                )
            
            # Get user data to verify user still exists and is active
            user_data = auth_service.get_user_by_username(username)
            if not user_data or not user_data.get("is_active", True):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"}
                )
            
            # Create a temporary session object for JWT-based requests
            from datetime import datetime, timezone
            try:
                user_role = UserRole(role_str)
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid user role"}
                )
            
            # Get client info for session
            ip_address = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            
            session = SessionInfo(
                session_id=session_id,  # Use JWT token as session ID
                user_id=user_data["id"],
                username=username,
                role=user_role,
                permissions=auth_service.get_default_permissions(user_role),
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                expires_at=datetime.fromtimestamp(jwt_payload.get("exp", 0), timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                status=SessionStatus.ACTIVE,
                is_temporary=True  # Flag to indicate this is a temporary session from JWT
            )
        
        # Update session activity (only for non-temporary sessions)
        if not getattr(session, 'is_temporary', False):
            session_manager.update_session_activity(session_id)
        
        # Add session info to request state
        request.state.session = session
        request.state.session_id = session_id
        
        # Log access
        logger.info(f"User {session.username} accessed {request.url.path}")
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Error processing request for user {session.username}: {str(e)}")
            raise
    
    def _extract_session_token(self, request: Request) -> Optional[str]:
        """Extract session token from request headers or cookies"""
        
        # Try session cookie first
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            return session_cookie
        
        # Try custom header
        session_header = request.headers.get("X-Session-ID")
        if session_header:
            return session_header
        
        # Try Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header.split(" ")[1]
        
        return None


class SessionDependency:
    """FastAPI dependency for session injection"""
    
    def __init__(self, require_permissions: List[str] = None):
        self.require_permissions = require_permissions or []
    
    async def __call__(self, request: Request) -> SessionInfo:
        """Get session from request state and validate permissions"""
        
        # First try to get session from middleware (if middleware was called)
        if hasattr(request.state, 'session'):
            session = request.state.session
        else:
            # Fallback: middleware wasn't called, so handle JWT validation here
            logger.warning(f"Middleware not called for {request.url.path}, handling JWT directly")
            
            # Extract JWT token
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No valid session found"
                )
            
            jwt_token = auth_header.split(" ")[1]
            
            # Validate JWT token
            jwt_payload = auth_service.verify_token(jwt_token)
            if not jwt_payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
            
            # Create temporary session from JWT
            username = jwt_payload.get("sub")
            role_str = jwt_payload.get("role")
            
            if not username or not role_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Get user data
            user_data = auth_service.get_user_by_username(username)
            if not user_data or not user_data.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            # Create temporary session
            from datetime import datetime, timezone
            try:
                user_role = UserRole(role_str)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user role"
                )
            
            session = SessionInfo(
                session_id=jwt_token,
                user_id=user_data["id"],
                username=username,
                role=user_role,
                permissions=auth_service.get_default_permissions(user_role),
                created_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                expires_at=datetime.fromtimestamp(jwt_payload.get("exp", 0), timezone.utc),
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
                status=SessionStatus.ACTIVE,
                is_temporary=True
            )
        
        # Check required permissions
        for permission in self.require_permissions:
            if not session_manager.validate_session_permission(session.session_id, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
        
        return session


class RoleBasedAccess:
    """Role-based access control dependency"""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, request: Request) -> SessionInfo:
        """Check if user has required role"""
        
        if not hasattr(request.state, 'session'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No valid session found"
            )
        
        session = request.state.session
        
        if session.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role permissions"
            )
        
        return session


# Dependency instances for common use cases
get_current_session = SessionDependency()
admin_required = RoleBasedAccess([UserRole.ADMIN])
lawyer_or_admin = RoleBasedAccess([UserRole.LAWYER, UserRole.ADMIN])
any_authenticated = SessionDependency()

# Permission-based dependencies
read_clients_required = SessionDependency(["read_own_clients", "read_all_clients"])
write_clients_required = SessionDependency(["write_own_clients", "write_all_clients"])
delete_clients_required = SessionDependency(["delete_clients"])
manage_users_required = SessionDependency(["manage_users"])
view_reports_required = SessionDependency(["view_reports"])
export_data_required = SessionDependency(["export_data"])


class SessionAPI:
    """API endpoints for session management"""
    
    @staticmethod
    async def get_current_session_info(session: SessionInfo) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "session_id": session.session_id,
            "username": session.username,
            "role": session.role.value,
            "permissions": session.permissions,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "expires_at": session.expires_at.isoformat(),
            "is_active": session.is_active()
        }
    
    @staticmethod
    async def extend_current_session(session: SessionInfo, 
                                   extension_hours: int = None) -> Dict[str, Any]:
        """Extend current session"""
        success = session_manager.extend_session(session.session_id, extension_hours)
        if success:
            updated_session = session_manager.get_session(session.session_id)
            return {
                "success": True,
                "new_expires_at": updated_session.expires_at.isoformat()
            }
        return {"success": False, "error": "Failed to extend session"}
    
    @staticmethod
    async def get_user_sessions(session: SessionInfo) -> List[Dict[str, Any]]:
        """Get all sessions for current user"""
        if session.role != UserRole.ADMIN:
            user_sessions = session_manager.get_user_sessions(session.user_id)
        else:
            # Admin can see session statistics
            stats = session_manager.get_session_statistics()
            return {"statistics": stats}
        
        return [
            {
                "session_id": s.session_id,
                "created_at": s.created_at.isoformat(),
                "last_activity": s.last_activity.isoformat(),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_current": s.session_id == session.session_id
            }
            for s in user_sessions
        ]
    
    @staticmethod
    async def terminate_session(session: SessionInfo, 
                              target_session_id: str) -> Dict[str, Any]:
        """Terminate a specific session"""
        
        # Users can only terminate their own sessions (except admins)
        if session.role != UserRole.ADMIN:
            user_sessions = session_manager.get_user_sessions(session.user_id)
            if not any(s.session_id == target_session_id for s in user_sessions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Can only terminate your own sessions"
                )
        
        success = session_manager.terminate_session(target_session_id)
        return {"success": success}
    
    @staticmethod
    async def terminate_other_sessions(session: SessionInfo) -> Dict[str, Any]:
        """Terminate all other sessions for current user"""
        
        terminated_count = session_manager.terminate_user_sessions(
            session.user_id, 
            exclude_session_id=session.session_id
        )
        
        return {
            "success": True,
            "terminated_sessions": terminated_count
        }


class AuditLogger:
    """Audit logging for session activities"""
    
    @staticmethod
    def log_session_event(session: SessionInfo, event: str, 
                         details: Dict[str, Any] = None):
        """Log session-related events"""
        
        log_entry = {
            "timestamp": session.last_activity.isoformat(),
            "session_id": session.session_id,
            "user_id": session.user_id,
            "username": session.username,
            "role": session.role.value,
            "event": event,
            "ip_address": session.ip_address,
            "details": details or {}
        }
        
        # In production, this would go to a proper audit log system
        logger.info(f"AUDIT: {json.dumps(log_entry)}")
    
    @staticmethod
    def log_access_attempt(ip_address: str, user_agent: str, 
                          username: str, success: bool, 
                          failure_reason: str = None):
        """Log authentication attempts"""
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "username": username,
            "event": "authentication_attempt",
            "success": success,
            "failure_reason": failure_reason
        }
        
        logger.info(f"AUTH_AUDIT: {json.dumps(log_entry)}")


# Session cleanup task (would be run as background task)
async def cleanup_expired_sessions():
    """Background task to clean up expired sessions"""
    try:
        cleaned_count = session_manager.cleanup_expired_sessions()
        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count
    except Exception as e:
        logger.error(f"Error during session cleanup: {str(e)}")
        return 0