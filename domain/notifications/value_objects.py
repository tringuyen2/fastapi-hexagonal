# domain/notifications/value_objects.py
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from core.exceptions import ValidationError


class NotificationChannel(Enum):
    """Notification channel enumeration"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


@dataclass(frozen=True)
class NotificationId:
    """Notification ID value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("Notification ID cannot be empty", "notification_id")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Recipient:
    """Recipient value object"""
    value: str
    channel: NotificationChannel
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("Recipient cannot be empty", "recipient")
        
        # Validate based on channel
        if self.channel == NotificationChannel.EMAIL:
            if "@" not in self.value:
                raise ValidationError("Invalid email recipient", "recipient")
        elif self.channel == NotificationChannel.SMS:
            if not self.value.replace("+", "").replace("-", "").replace(" ", "").isdigit():
                raise ValidationError("Invalid phone number recipient", "recipient")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class NotificationContent:
    """Notification content value object"""
    subject: str
    body: str
    template_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.subject.strip():
            raise ValidationError("Subject cannot be empty", "subject")
        if not self.body.strip():
            raise ValidationError("Body cannot be empty", "body")
        if len(self.subject) > 500:
            raise ValidationError("Subject cannot exceed 500 characters", "subject")