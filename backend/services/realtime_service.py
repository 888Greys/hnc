#!/usr/bin/env python3
"""
Real-time WebSocket Service for HNC Legal Questionnaire
Provides real-time notifications, live updates, and collaborative features
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of real-time notifications"""
    CLIENT_CREATED = "client_created"
    CLIENT_UPDATED = "client_updated"
    AI_SUGGESTION_READY = "ai_suggestion_ready"
    DOCUMENT_GENERATED = "document_generated"
    USER_ACTIVITY = "user_activity"
    SYSTEM_ALERT = "system_alert"
    FORM_AUTO_SAVE = "form_auto_save"
    COLLABORATION_UPDATE = "collaboration_update"
    # Enhanced legal process notifications
    WILL_DRAFT_READY = "will_draft_ready"
    TRUST_SETUP_COMPLETE = "trust_setup_complete"
    ASSET_VALUATION_REQUIRED = "asset_valuation_required"
    COMPLIANCE_DEADLINE = "compliance_deadline"
    DOCUMENT_SIGNING_REQUIRED = "document_signing_required"
    BENEFICIARY_VERIFICATION_NEEDED = "beneficiary_verification_needed"
    TAX_IMPLICATION_ALERT = "tax_implication_alert"
    PROBATE_STATUS_UPDATE = "probate_status_update"
    LEGAL_MILESTONE_REACHED = "legal_milestone_reached"


class Priority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class RealTimeNotification:
    """Real-time notification data structure"""
    id: str
    type: NotificationType
    priority: Priority
    title: str
    message: str
    data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    client_id: Optional[str] = None
    created_at: str = None
    expires_at: Optional[str] = None
    read: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.expires_at is None:
            # Default expiry: 24 hours for low priority, 7 days for high priority
            hours = 24 if self.priority in [Priority.LOW, Priority.MEDIUM] else 168
            self.expires_at = (datetime.now() + timedelta(hours=hours)).isoformat()


@dataclass
class UserSession:
    """User session for WebSocket management"""
    user_id: str
    username: str
    role: str
    websocket: WebSocket
    connected_at: str
    last_activity: str
    active_client_id: Optional[str] = None
    
    def __post_init__(self):
        if self.connected_at is None:
            self.connected_at = datetime.now().isoformat()
        if self.last_activity is None:
            self.last_activity = datetime.now().isoformat()


class RealTimeService:
    """Service for managing real-time WebSocket connections and notifications"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.active_connections: Dict[str, UserSession] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.notification_handlers: Dict[NotificationType, List] = {}
        self.auto_save_intervals: Dict[str, asyncio.Task] = {}
        
    async def initialize(self):
        """Initialize Redis connection and setup"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                retry_on_timeout=True
            )
            await self.redis_client.ping()
            logger.info("Real-time service initialized successfully")
            
            # Start background tasks
            asyncio.create_task(self._cleanup_expired_notifications())
            asyncio.create_task(self._monitor_user_activity())
            
        except Exception as e:
            logger.error(f"Failed to initialize real-time service: {e}")
            self.redis_client = None
    
    async def connect_user(self, websocket: WebSocket, user_id: str, username: str, role: str) -> str:
        """Connect a user via WebSocket"""
        await websocket.accept()
        
        connection_id = f"{user_id}_{datetime.now().timestamp()}"
        session = UserSession(
            user_id=user_id,
            username=username,
            role=role,
            websocket=websocket,
            connected_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat()
        )
        
        self.active_connections[connection_id] = session
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        # Send welcome message
        await self._send_to_connection(connection_id, {
            "type": "connection_established",
            "message": f"Welcome {username}! Real-time updates enabled.",
            "connection_id": connection_id,
            "user_info": {
                "user_id": user_id,
                "username": username,
                "role": role
            }
        })
        
        # Send pending notifications
        await self._send_pending_notifications(user_id)
        
        # Notify other users about new connection
        await self.broadcast_user_activity(
            user_id, username, "connected", exclude_user=user_id
        )
        
        logger.info(f"User {username} ({user_id}) connected via WebSocket")
        return connection_id
    
    async def disconnect_user(self, connection_id: str):
        """Disconnect a user WebSocket"""
        if connection_id in self.active_connections:
            session = self.active_connections[connection_id]
            user_id = session.user_id
            username = session.username
            
            # Remove connection
            del self.active_connections[connection_id]
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Cancel auto-save task if exists
            if connection_id in self.auto_save_intervals:
                self.auto_save_intervals[connection_id].cancel()
                del self.auto_save_intervals[connection_id]
            
            # Notify other users about disconnection
            await self.broadcast_user_activity(
                user_id, username, "disconnected", exclude_user=user_id
            )
            
            logger.info(f"User {username} ({user_id}) disconnected")
    
    async def send_notification(self, notification: RealTimeNotification):
        """Send a real-time notification"""
        try:
            # Store notification in Redis
            if self.redis_client:
                await self.redis_client.setex(
                    f"notification:{notification.id}",
                    timedelta(days=7).total_seconds(),
                    json.dumps(asdict(notification))
                )
            
            # Send to specific user or broadcast
            if notification.user_id:
                await self._send_to_user(notification.user_id, {
                    "type": "notification",
                    "notification": asdict(notification)
                })
            else:
                await self._broadcast_message({
                    "type": "notification",
                    "notification": asdict(notification)
                })
            
            logger.info(f"Sent notification: {notification.type.value} to {notification.user_id or 'all users'}")
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def broadcast_user_activity(self, user_id: str, username: str, activity: str, exclude_user: str = None):
        """Broadcast user activity to other connected users"""
        message = {
            "type": "user_activity",
            "data": {
                "user_id": user_id,
                "username": username,
                "activity": activity,
                "timestamp": datetime.now().isoformat()
            }
        }
        
        for conn_id, session in self.active_connections.items():
            if exclude_user and session.user_id == exclude_user:
                continue
            await self._send_to_connection(conn_id, message)
    
    async def start_auto_save(self, connection_id: str, client_id: str, interval_seconds: int = 30):
        """Start auto-save for a user's form"""
        if connection_id in self.auto_save_intervals:
            self.auto_save_intervals[connection_id].cancel()
        
        async def auto_save_task():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    if connection_id in self.active_connections:
                        await self._send_to_connection(connection_id, {
                            "type": "auto_save_trigger",
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        })
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Auto-save error for {connection_id}: {e}")
        
        self.auto_save_intervals[connection_id] = asyncio.create_task(auto_save_task())
        logger.info(f"Started auto-save for connection {connection_id} with {interval_seconds}s interval")
    
    async def stop_auto_save(self, connection_id: str):
        """Stop auto-save for a user's form"""
        if connection_id in self.auto_save_intervals:
            self.auto_save_intervals[connection_id].cancel()
            del self.auto_save_intervals[connection_id]
            logger.info(f"Stopped auto-save for connection {connection_id}")
    
    async def update_user_activity(self, connection_id: str, activity_data: Dict[str, Any]):
        """Update user activity and broadcast to relevant users"""
        if connection_id in self.active_connections:
            session = self.active_connections[connection_id]
            session.last_activity = datetime.now().isoformat()
            
            # Update active client if provided
            if "client_id" in activity_data:
                session.active_client_id = activity_data["client_id"]
            
            # Broadcast activity to other users working on the same client
            if session.active_client_id:
                message = {
                    "type": "collaboration_update",
                    "data": {
                        "user_id": session.user_id,
                        "username": session.username,
                        "client_id": session.active_client_id,
                        "activity": activity_data,
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                for conn_id, other_session in self.active_connections.items():
                    if (conn_id != connection_id and 
                        other_session.active_client_id == session.active_client_id):
                        await self._send_to_connection(conn_id, message)
    
    async def get_active_users(self) -> List[Dict[str, Any]]:
        """Get list of currently active users"""
        users = {}
        for session in self.active_connections.values():
            if session.user_id not in users:
                users[session.user_id] = {
                    "user_id": session.user_id,
                    "username": session.username,
                    "role": session.role,
                    "connected_at": session.connected_at,
                    "last_activity": session.last_activity,
                    "active_client_id": session.active_client_id,
                    "connections": 1
                }
            else:
                users[session.user_id]["connections"] += 1
                # Update to most recent activity
                if session.last_activity > users[session.user_id]["last_activity"]:
                    users[session.user_id]["last_activity"] = session.last_activity
        
        return list(users.values())
    
    async def _send_to_user(self, user_id: str, message: Dict[str, Any]):
        """Send message to all connections of a specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self._send_to_connection(connection_id, message)
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """Send message to a specific connection"""
        if connection_id in self.active_connections:
            try:
                session = self.active_connections[connection_id]
                await session.websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                # Clean up broken connection
                await self.disconnect_user(connection_id)
    
    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected users"""
        for connection_id in list(self.active_connections.keys()):
            await self._send_to_connection(connection_id, message)
    
    async def _send_pending_notifications(self, user_id: str):
        """Send pending notifications to a newly connected user"""
        if not self.redis_client:
            return
        
        try:
            # Get user's pending notifications
            keys = await self.redis_client.keys(f"notification:*")
            for key in keys:
                notification_data = await self.redis_client.get(key)
                if notification_data:
                    notification = json.loads(notification_data)
                    if (notification.get("user_id") == user_id and 
                        not notification.get("read", False)):
                        await self._send_to_user(user_id, {
                            "type": "notification",
                            "notification": notification
                        })
        except Exception as e:
            logger.error(f"Failed to send pending notifications: {e}")
    
    async def _cleanup_expired_notifications(self):
        """Background task to cleanup expired notifications"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                if self.redis_client:
                    now = datetime.now()
                    keys = await self.redis_client.keys("notification:*")
                    
                    for key in keys:
                        notification_data = await self.redis_client.get(key)
                        if notification_data:
                            notification = json.loads(notification_data)
                            expires_at = datetime.fromisoformat(notification["expires_at"])
                            if now > expires_at:
                                await self.redis_client.delete(key)
                
                logger.info("Completed notification cleanup")
            except Exception as e:
                logger.error(f"Error in notification cleanup: {e}")
    
    async def _monitor_user_activity(self):
        """Background task to monitor user activity and detect idle users"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                now = datetime.now()
                idle_threshold = timedelta(minutes=30)
                
                for connection_id, session in list(self.active_connections.items()):
                    last_activity = datetime.fromisoformat(session.last_activity)
                    if now - last_activity > idle_threshold:
                        # Send idle warning
                        await self._send_to_connection(connection_id, {
                            "type": "idle_warning",
                            "message": "You've been idle for 30 minutes. Your session may expire soon.",
                            "timestamp": datetime.now().isoformat()
                        })
                
            except Exception as e:
                logger.error(f"Error in activity monitoring: {e}")


# Global real-time service instance
realtime_service = RealTimeService()


# Utility functions for common notifications
async def notify_client_created(client_id: str, client_name: str, created_by: str):
    """Send notification when a new client is created with real client data"""
    try:
        # Import here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        # Load real client data
        def load_client_data_local(client_id: str) -> dict:
            try:
                import json
                import os
                data_dir = os.getenv("DATA_DIR", "data")
                client_file_path = os.path.join(data_dir, "clients", f"{client_id}.json")
                if os.path.exists(client_file_path):
                    with open(client_file_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                return {}
            except Exception as e:
                logger.error(f"Error loading client data: {e}")
                return {}
        
        client_data = load_client_data_local(client_id)
        
        # Extract real client information
        bio_data = client_data.get('bioData', {})
        financial_data = client_data.get('financialData', {})
        objectives = client_data.get('objectives', {})
        
        objective = objectives.get('objective', 'Unknown')
        marital_status = bio_data.get('maritalStatus', 'Unknown')
        assets = financial_data.get('assets', [])
        total_asset_value = sum(asset.get('value', 0) for asset in assets)
        
        # Determine notification priority based on case complexity
        priority = Priority.HIGH if total_asset_value > 10000000 else Priority.MEDIUM  # 10M KES threshold
        
        notification = RealTimeNotification(
            id=f"client_created_{client_id}_{int(datetime.now().timestamp())}",
            type=NotificationType.CLIENT_CREATED,
            priority=priority,
            title="New Client Registered",
            message=f"Client '{client_name}' registered with {objective.lower()} objective (Assets: KES {total_asset_value:,})",
            data={
                "client_id": client_id,
                "client_name": client_name,
                "objective": objective,
                "created_by": created_by,
                "asset_count": len(assets),
                "total_asset_value": total_asset_value,
                "marital_status": marital_status,
                "complexity_level": "high" if total_asset_value > 10000000 else "medium",
                "legal_considerations": {
                    "inheritance_tax_applicable": total_asset_value > 5000000,  # 5M KES threshold
                    "probate_required": objective in ['Create Will', 'Create Trust'],
                    "asset_valuation_needed": len(assets) > 3
                }
            },
            user_id=created_by
        )
        await realtime_service.send_notification(notification)
        
        # Broadcast to legal team members for high-value cases
        if total_asset_value > 10000000:
            await realtime_service.broadcast_user_activity(
                created_by, created_by, 
                f"registered high-value client: {client_name} (KES {total_asset_value:,})"
            )
            
        logger.info(f"Enhanced notification sent for client {client_id} with real data")
        
    except Exception as e:
        logger.error(f"Error in enhanced notify_client_created: {e}")
        # Fallback to basic notification
        notification = RealTimeNotification(
            id=f"client_created_{client_id}_{int(datetime.now().timestamp())}",
            type=NotificationType.CLIENT_CREATED,
            priority=Priority.MEDIUM,
            title="New Client Created",
            message=f"Client '{client_name}' has been created by {created_by}",
            data={"client_id": client_id, "client_name": client_name, "created_by": created_by}
        )
        await realtime_service.send_notification(notification)


async def notify_ai_suggestion_ready(client_id: str, user_id: str):
    """Send notification when AI suggestion is ready"""
    notification = RealTimeNotification(
        id=f"ai_ready_{client_id}_{int(datetime.now().timestamp())}",
        type=NotificationType.AI_SUGGESTION_READY,
        priority=Priority.HIGH,
        title="AI Suggestion Ready",
        message="AI analysis and legal suggestions are now available",
        data={"client_id": client_id},
        user_id=user_id
    )
    await realtime_service.send_notification(notification)


async def notify_document_generated(document_id: str, document_type: str, user_id: str):
    """Send notification when a document is generated"""
    notification = RealTimeNotification(
        id=f"doc_generated_{document_id}_{int(datetime.now().timestamp())}",
        type=NotificationType.DOCUMENT_GENERATED,
        priority=Priority.HIGH,
        title="Document Generated",
        message=f"{document_type} document has been generated successfully",
        data={"document_id": document_id, "document_type": document_type},
        user_id=user_id
    )
    await realtime_service.send_notification(notification)


async def notify_system_alert(message: str, priority: Priority = Priority.MEDIUM):
    """Send system-wide alert notification"""
    notification = RealTimeNotification(
        id=f"system_alert_{int(datetime.now().timestamp())}",
        type=NotificationType.SYSTEM_ALERT,
        priority=priority,
        title="System Alert",
        message=message,
        data={"alert_time": datetime.now().isoformat()}
    )
    await realtime_service.send_notification(notification)


async def notify_legal_milestone_reached(client_id: str, milestone: str, user_id: str):
    """Send notification when a legal milestone is reached with real client context"""
    try:
        # Load real client data for context
        import json
        import os
        data_dir = os.getenv("DATA_DIR", "data")
        client_file_path = os.path.join(data_dir, "clients", f"{client_id}.json")
        
        client_data = {}
        if os.path.exists(client_file_path):
            with open(client_file_path, "r", encoding="utf-8") as f:
                client_data = json.load(f)
        
        client_name = client_data.get('bioData', {}).get('fullName', 'Unknown Client')
        objective = client_data.get('objectives', {}).get('objective', 'Unknown')
        assets = client_data.get('financialData', {}).get('assets', [])
        total_value = sum(asset.get('value', 0) for asset in assets)
        
        # Determine next steps based on milestone and real data
        next_steps = []
        legal_implications = []
        
        if milestone == "will_drafted":
            next_steps = [
                "Schedule will review with client",
                "Arrange witness signing appointment",
                "Prepare probate documentation"
            ]
            legal_implications = [
                f"Inheritance tax applicable: {total_value > 5000000}",
                "Probate registration required",
                "Asset valuation documentation needed"
            ]
        elif milestone == "trust_established":
            next_steps = [
                "Transfer assets to trust",
                "Establish trust management protocols",
                "Setup beneficiary communications"
            ]
            legal_implications = [
                "Trust tax obligations apply",
                "Asset transfer documentation required",
                "Ongoing fiduciary responsibilities"
            ]
        
        priority = Priority.HIGH if total_value > 10000000 else Priority.MEDIUM
        
        notification = RealTimeNotification(
            id=f"milestone_{milestone}_{client_id}_{int(datetime.now().timestamp())}",
            type=NotificationType.LEGAL_MILESTONE_REACHED,
            priority=priority,
            title=f"Legal Milestone: {milestone.replace('_', ' ').title()}",
            message=f"Milestone '{milestone}' reached for {client_name} ({objective})",
            data={
                "client_id": client_id,
                "client_name": client_name,
                "milestone": milestone,
                "objective": objective,
                "asset_value": total_value,
                "next_steps": next_steps,
                "legal_implications": legal_implications,
                "completion_percentage": calculate_completion_percentage(milestone, objective)
            },
            user_id=user_id
        )
        await realtime_service.send_notification(notification)
        
    except Exception as e:
        logger.error(f"Error in notify_legal_milestone_reached: {e}")


async def notify_compliance_deadline(client_id: str, deadline_type: str, days_remaining: int, user_id: str):
    """Send notification about approaching compliance deadlines"""
    try:
        # Load client data for context
        import json
        import os
        data_dir = os.getenv("DATA_DIR", "data")
        client_file_path = os.path.join(data_dir, "clients", f"{client_id}.json")
        
        client_data = {}
        if os.path.exists(client_file_path):
            with open(client_file_path, "r", encoding="utf-8") as f:
                client_data = json.load(f)
        
        client_name = client_data.get('bioData', {}).get('fullName', 'Unknown Client')
        
        priority = Priority.URGENT if days_remaining <= 7 else Priority.HIGH if days_remaining <= 30 else Priority.MEDIUM
        
        notification = RealTimeNotification(
            id=f"compliance_{deadline_type}_{client_id}_{int(datetime.now().timestamp())}",
            type=NotificationType.COMPLIANCE_DEADLINE,
            priority=priority,
            title=f"Compliance Deadline: {deadline_type}",
            message=f"{deadline_type} deadline for {client_name} in {days_remaining} days",
            data={
                "client_id": client_id,
                "client_name": client_name,
                "deadline_type": deadline_type,
                "days_remaining": days_remaining,
                "urgency_level": "urgent" if days_remaining <= 7 else "high" if days_remaining <= 30 else "medium",
                "required_actions": get_compliance_actions(deadline_type),
                "legal_consequences": get_legal_consequences(deadline_type)
            },
            user_id=user_id
        )
        await realtime_service.send_notification(notification)
        
    except Exception as e:
        logger.error(f"Error in notify_compliance_deadline: {e}")


async def notify_asset_valuation_required(client_id: str, asset_type: str, reason: str, user_id: str):
    """Send notification when asset valuation is required"""
    try:
        import json
        import os
        data_dir = os.getenv("DATA_DIR", "data")
        client_file_path = os.path.join(data_dir, "clients", f"{client_id}.json")
        
        client_data = {}
        if os.path.exists(client_file_path):
            with open(client_file_path, "r", encoding="utf-8") as f:
                client_data = json.load(f)
        
        client_name = client_data.get('bioData', {}).get('fullName', 'Unknown Client')
        
        notification = RealTimeNotification(
            id=f"valuation_{asset_type}_{client_id}_{int(datetime.now().timestamp())}",
            type=NotificationType.ASSET_VALUATION_REQUIRED,
            priority=Priority.HIGH,
            title=f"Asset Valuation Required: {asset_type}",
            message=f"Professional valuation needed for {client_name}'s {asset_type} - {reason}",
            data={
                "client_id": client_id,
                "client_name": client_name,
                "asset_type": asset_type,
                "reason": reason,
                "estimated_cost": get_valuation_cost_estimate(asset_type),
                "recommended_valuers": get_recommended_valuers(asset_type),
                "legal_requirement": is_legal_requirement(asset_type, reason)
            },
            user_id=user_id
        )
        await realtime_service.send_notification(notification)
        
    except Exception as e:
        logger.error(f"Error in notify_asset_valuation_required: {e}")


def calculate_completion_percentage(milestone: str, objective: str) -> int:
    """Calculate completion percentage based on milestone and objective"""
    completion_map = {
        ('Create Will', 'client_registered'): 10,
        ('Create Will', 'assets_documented'): 30,
        ('Create Will', 'beneficiaries_identified'): 50,
        ('Create Will', 'will_drafted'): 75,
        ('Create Will', 'will_signed'): 90,
        ('Create Will', 'probate_registered'): 100,
        
        ('Create Trust', 'client_registered'): 10,
        ('Create Trust', 'trust_structure_designed'): 25,
        ('Create Trust', 'trustees_appointed'): 40,
        ('Create Trust', 'trust_deed_drafted'): 60,
        ('Create Trust', 'trust_established'): 80,
        ('Create Trust', 'assets_transferred'): 100
    }
    
    return completion_map.get((objective, milestone), 0)


def get_compliance_actions(deadline_type: str) -> list:
    """Get required actions for compliance deadlines"""
    actions_map = {
        "tax_filing": [
            "Prepare tax documentation",
            "Calculate inheritance tax liability",
            "Submit tax returns to KRA"
        ],
        "probate_registration": [
            "Compile probate documentation",
            "Submit application to High Court",
            "Pay probate fees"
        ],
        "trust_reporting": [
            "Prepare trust annual returns",
            "Document beneficiary distributions",
            "Submit regulatory filings"
        ]
    }
    return actions_map.get(deadline_type, ["Contact legal counsel for guidance"])


def get_legal_consequences(deadline_type: str) -> list:
    """Get legal consequences of missing deadlines"""
    consequences_map = {
        "tax_filing": [
            "Penalties and interest charges",
            "Potential asset freezing",
            "Legal action by tax authorities"
        ],
        "probate_registration": [
            "Delays in asset distribution",
            "Additional court fees",
            "Potential beneficiary disputes"
        ],
        "trust_reporting": [
            "Regulatory penalties",
            "Trust compliance violations",
            "Potential trust dissolution"
        ]
    }
    return consequences_map.get(deadline_type, ["Legal complications may arise"])


def get_valuation_cost_estimate(asset_type: str) -> str:
    """Get estimated cost for asset valuation"""
    cost_map = {
        "Real Estate": "KES 50,000 - 150,000",
        "Business": "KES 100,000 - 500,000",
        "Shares": "KES 25,000 - 75,000",
        "Other": "KES 30,000 - 100,000"
    }
    return cost_map.get(asset_type, "Contact professional valuers for quote")


def get_recommended_valuers(asset_type: str) -> list:
    """Get recommended professional valuers"""
    valuers_map = {
        "Real Estate": [
            "Institute of Surveyors of Kenya (ISK) members",
            "Licensed property valuers",
            "Real estate appraisal firms"
        ],
        "Business": [
            "Certified business valuers",
            "Audit firms with valuation services",
            "Financial advisory consultants"
        ],
        "Shares": [
            "Stock exchange approved valuers",
            "Investment banking firms",
            "Financial analysts"
        ]
    }
    return valuers_map.get(asset_type, ["Contact professional valuation services"])


def is_legal_requirement(asset_type: str, reason: str) -> bool:
    """Check if valuation is legally required"""
    legal_requirements = {
        "inheritance_tax": True,
        "probate_application": True,
        "trust_establishment": True,
        "court_order": True,
        "regulatory_compliance": True
    }
    return legal_requirements.get(reason, False)