from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    PAYMENT_PROCESS = "payment.process"
    NOTIFICATION_SEND = "notification.send"


class EventStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class EventMessage(BaseModel):
    """Base event message model"""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: EventType = Field(..., description="Type of event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Event source (http, kafka, celery)")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HandlerResult(BaseModel):
    """Result from handler execution"""
    success: bool
    status: EventStatus
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    execution_time_ms: Optional[float] = None


class UserCreateData(BaseModel):
    """User creation data model"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    age: Optional[int] = Field(None, ge=0, le=120)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentProcessData(BaseModel):
    """Payment processing data model"""
    user_id: str
    amount: float = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: str
    reference: Optional[str] = None


class NotificationData(BaseModel):
    """Notification data model"""
    recipient: str
    subject: str
    body: str
    channel: str = Field(default="email")  # email, sms, push
    template_id: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)