from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import uuid
from datetime import datetime

from core.models import EventMessage, HandlerResult, EventType, EventStatus
from core.registry import registry
from core.exceptions import HandlerNotFoundException
from loguru import logger


class BaseAdapter(ABC):
    """Base class for all adapters"""
    
    def __init__(self, adapter_name: str):
        self.adapter_name = adapter_name
        self.registry = registry
    
    @abstractmethod
    async def start(self) -> None:
        """Start the adapter"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the adapter"""
        pass
    
    async def process_event(
        self, 
        event_type: EventType, 
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> HandlerResult:
        """Process event through appropriate handler"""
        
        # Create event message
        event = EventMessage(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source=self.adapter_name,
            correlation_id=correlation_id,
            data=data,
            metadata=metadata or {}
        )
        
        try:
            # Get handler for event type
            handler = self.registry.get_handler(event_type)
            
            # Execute handler
            result = await handler.execute(event)
            
            logger.info(
                f"Event {event.event_id} processed by {self.adapter_name}: "
                f"success={result.success}, status={result.status}"
            )
            
            return result
            
        except HandlerNotFoundException as e:
            logger.error(f"No handler found for event type {event_type}: {e}")
            return HandlerResult(
                success=False,
                status=EventStatus.FAILED,
                message=str(e),
                error_code=e.error_code
            )
        except Exception as e:
            logger.error(f"Unexpected error processing event {event.event_id}: {e}")
            return HandlerResult(
                success=False,
                status=EventStatus.FAILED,
                message=f"Unexpected error: {str(e)}",
                error_code="ADAPTER_ERROR"
            )