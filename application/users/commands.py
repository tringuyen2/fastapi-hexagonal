# application/users/commands.py (Fix Pydantic v2)
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class CreateUserCommand(BaseModel):
    """Command to create a new user"""
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
    correlation_id: Optional[str] = None


class UpdateUserCommand(BaseModel):
    """Command to update a user"""
    user_id: str = Field(..., min_length=1)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    metadata: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class DeleteUserCommand(BaseModel):
    """Command to delete a user"""
    user_id: str = Field(..., min_length=1)
    correlation_id: Optional[str] = None
