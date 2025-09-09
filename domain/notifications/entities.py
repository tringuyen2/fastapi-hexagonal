# domain/notifications/entities.py (Fixed missing import)
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .value_objects import NotificationId, Recipient, NotificationContent
from ..users.value_objects import UserId
from core.exceptions import BusinessRuleViolationError  # Added missing import


class NotificationStatus(Enum):
    """Notification status enumeration"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Notification:
    """Notification domain entity"""
    notification_id: NotificationId
    recipient: Recipient
    content: NotificationContent
    user_id: Optional[UserId] = None
    status: NotificationStatus = NotificationStatus.PENDING
    external_id: Optional[str] = None  # ID from external service
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sent_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def mark_as_sent(self, external_id: Optional[str] = None) -> None:
        """Mark notification as sent"""
        self.status = NotificationStatus.SENT
        self.external_id = external_id
        self.sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.failure_reason = None
    
    def mark_as_delivered(self) -> None:
        """Mark notification as delivered"""
        if self.status != NotificationStatus.SENT:
            raise BusinessRuleViolationError(
                "Notification status transition",
                "Can only mark sent notifications as delivered"
            )
        self.status = NotificationStatus.DELIVERED
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, reason: str) -> None:
        """Mark notification as failed"""
        self.status = NotificationStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()
    
    def cancel(self) -> None:
        """Cancel notification"""
        if self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]:
            raise BusinessRuleViolationError(
                "Notification cancellation",
                "Cannot cancel already sent notifications"
            )
        self.status = NotificationStatus.CANCELLED
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "notification_id": str(self.notification_id),
            "recipient": str(self.recipient),
            "channel": self.recipient.channel.value,
            "subject": self.content.subject,
            "body": self.content.body,
            "template_id": self.content.template_id,
            "user_id": str(self.user_id) if self.user_id else None,
            "status": self.status.value,
            "external_id": self.external_id,
            "failure_reason": self.failure_reason,
            "metadata": self.metadata,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
