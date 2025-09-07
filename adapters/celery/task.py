# adapters/celery/tasks.py
from typing import Dict, Any, Optional
import asyncio
from celery import current_app
from loguru import logger

from core.models import EventType, HandlerResult
from core.registry import registry


# Get Celery app instance
celery = current_app


@celery.task(bind=True, name='adapters.celery.tasks.process_event_task')
def process_event_task(self, event_type: str, data: Dict[str, Any], 
                      correlation_id: Optional[str] = None, 
                      metadata: Dict[str, Any] = None) -> dict:
    """Celery task to process events"""
    try:
        logger.info(f"Processing event {event_type} in Celery task {self.request.id}")
        
        # Convert string to EventType enum
        event_type_enum = EventType(event_type)
        
        # Create adapter instance
        from adapters.celery.adapter import CeleryAdapter
        adapter = CeleryAdapter()
        
        # Process event (need to run in async context)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                adapter.process_event(
                    event_type=event_type_enum,
                    data=data,
                    correlation_id=correlation_id,
                    metadata=metadata
                )
            )
            
            logger.info(f"Event {event_type} processed successfully in task {self.request.id}")
            
            return {
                "success": result.success,
                "status": result.status.value,
                "message": result.message,
                "data": result.data,
                "error_code": result.error_code,
                "execution_time_ms": result.execution_time_ms
            }
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Task {self.request.id} failed: {str(e)}")
        
        # Retry logic
        if self.request.retries < 3:
            logger.info(f"Retrying task {self.request.id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        
        return {
            "success": False,
            "status": "failed",
            "message": str(e),
            "error_code": "CELERY_TASK_ERROR"
        }
