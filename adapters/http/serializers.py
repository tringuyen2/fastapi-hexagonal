from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from core.models import EventType, HandlerResult


class HTTPEventRequest(BaseModel):
    """HTTP event request model"""
    event_type: EventType = Field(..., description="Type of event to process")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracking")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class HTTPEventResponse(BaseModel):
    """HTTP event response model"""
    success: bool = Field(..., description="Whether the event was processed successfully")
    status: str = Field(..., description="Event processing status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    @classmethod
    def from_handler_result(cls, result: HandlerResult) -> "HTTPEventResponse":
        """Create response from handler result"""
        return cls(
            success=result.success,
            status=result.status.value,
            message=result.message,
            data=result.data,
            error_code=result.error_code,
            execution_time_ms=result.execution_time_ms
        )


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0")
    adapters: Dict[str, str] = Field(default_factory=dict)
