# adapters/inbound/http/serializers.py (Fix Pydantic v2 deprecation)
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    message: Optional[str] = Field(None, description="Response message")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class CreateUserRequest(BaseModel):
    """Create user request model"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 30,
                "metadata": {"department": "IT"}
            }
        }
    )
    
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    age: Optional[int] = Field(None, ge=0, le=150)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateUserRequest(BaseModel):
    """Update user request model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    metadata: Optional[Dict[str, Any]] = None


class ProcessPaymentRequest(BaseModel):
    """Process payment request model"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "amount": "99.99",
                "currency": "USD",
                "payment_method": "credit_card",
                "reference": "order_456"
            }
        }
    )
    
    user_id: str = Field(..., min_length=1)
    amount: str = Field(..., pattern=r'^\d+(\.\d{1,2})?$')  # String to avoid precision issues
    currency: str = Field(..., pattern=r'^[A-Z]{3}$')
    payment_method: str = Field(..., min_length=1)
    reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SendNotificationRequest(BaseModel):
    """Send notification request model"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipient": "user@example.com",
                "channel": "email",
                "subject": "Welcome!",
                "body": "Hello {name}, welcome!",
                "variables": {"name": "John"}
            }
        }
    )
    
    recipient: str = Field(..., min_length=1)
    channel: str = Field(..., pattern=r'^(email|sms|push|webhook)$')
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    user_id: Optional[str] = None
    template_id: Optional[str] = None
    variables: Dict[str, Any] = Field(default_factory=dict)
