# application/notifications/commands.py (Fix Pydantic v2)  
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SendNotificationCommand(BaseModel):
    """Command to send a notification"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recipient": "user@example.com",
                "channel": "email",
                "subject": "Welcome!",
                "body": "Hello {name}, welcome to our platform!",
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
    correlation_id: Optional[str] = None
