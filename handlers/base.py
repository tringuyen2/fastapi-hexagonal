from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import time
import uuid
from loguru import logger

from core.models import EventMessage, HandlerResult, EventStatus
from core.exceptions import HandlerExecutionException


class BaseHandler(ABC):
    """Base class for all event handlers"""
    
    def __init__(self):
        self.handler_name = self.__class__.__name__
    
    @abstractmethod
    async def handle(self, event: EventMessage) -> HandlerResult:
        """Handle the event - must be implemented by subclasses"""
        pass
    
    async def execute(self, event: EventMessage) -> HandlerResult:
        """Execute handler with error handling and metrics"""
        start_time = time.time()
        
        try:
            logger.info(f"Executing handler {self.handler_name} for event {event.event_id}")
            
            # Validate event
            await self._validate_event(event)
            
            # Execute the actual handler logic
            result = await self.handle(event)
            
            # Calculate execution time
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            logger.info(
                f"Handler {self.handler_name} completed successfully in {execution_time:.2f}ms"
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            logger.error(
                f"Handler {self.handler_name} failed after {execution_time:.2f}ms: {error_msg}"
            )
            
            return HandlerResult(
                success=False,
                status=EventStatus.FAILED,
                message=error_msg,
                error_code="HANDLER_EXECUTION_ERROR",
                execution_time_ms=execution_time
            )
    
    async def _validate_event(self, event: EventMessage) -> None:
        """Validate event data - can be overridden by subclasses"""
        if not event.event_id:
            raise ValueError("Event ID is required")
        
        if not event.event_type:
            raise ValueError("Event type is required")
    
    def _create_success_result(
        self, 
        message: str = "Handler executed successfully", 
        data: Optional[Dict[str, Any]] = None
    ) -> HandlerResult:
        """Helper to create success result"""
        return HandlerResult(
            success=True,
            status=EventStatus.SUCCESS,
            message=message,
            data=data or {}
        )
    
    def _create_failure_result(
        self, 
        message: str, 
        error_code: str = "HANDLER_ERROR"
    ) -> HandlerResult:
        """Helper to create failure result"""
        return HandlerResult(
            success=False,
            status=EventStatus.FAILED,
            message=message,
            error_code=error_code
        )