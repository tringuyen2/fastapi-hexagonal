# adapters/inbound/celery/tasks.py
from typing import Dict, Any, Optional
import asyncio
from celery import current_task
from loguru import logger

from .worker import celery_app
from core.registry import registry, HandlerType


@celery_app.task(bind=True, name='process_user_command')
def process_user_command(self, data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """Celery task to process user commands"""
    return _run_async_handler("create_user", data, {
        "task_id": self.request.id,
        "correlation_id": correlation_id,
        "retries": self.request.retries
    })


@celery_app.task(bind=True, name='process_payment_command')
def process_payment_command(self, data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
    """Celery task to process payment commands"""
    return _run_async_handler("process_payment", data, {
        "task_id": self.request.id,
        "correlation_id": correlation_id,
        "retries": self.request.retries
    })


def _run_async_handler(operation: str, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to run async handlers in Celery tasks"""
    try:
        logger.info(f"Processing Celery task: {operation} (task_id: {context.get('task_id')})")
        
        # Get handler from registry
        handler = registry.get_handler(operation, HandlerType.CELERY)
        
        # Run async handler in new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(handler.handle(data, context))
            logger.info(f"Celery task completed: {operation} (success: {result.get('success')})")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Celery task failed: {operation} - {str(e)}")
        
        # Retry logic
        task = current_task
        if task and task.request.retries < 3:
            logger.info(f"Retrying task {operation}, attempt {task.request.retries + 1}")
            raise task.retry(countdown=60 * (task.request.retries + 1))
        
        return {
            "success": False,
            "error_code": "CELERY_TASK_ERROR",
            "message": str(e)
        }