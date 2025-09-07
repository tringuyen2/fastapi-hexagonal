# adapters/celery/adapter.py
from typing import Dict, Any, Optional
import json
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from kombu import Queue

from adapters.base_adapter import BaseAdapter
from core.models import EventType, HandlerResult
from core.config import load_config
from loguru import logger


class CeleryAdapter(BaseAdapter):
    """Celery adapter for task queue processing"""
    
    def __init__(self):
        super().__init__("celery")
        self.config = load_config()
        self.celery_app = None
        self._setup_celery()
    
    def _setup_celery(self):
        """Setup Celery application"""
        self.celery_app = Celery(
            'event-manager',
            broker=self.config.redis.url,
            backend=self.config.redis.url,
            include=['adapters.celery.tasks']
        )
        
        # Configure Celery
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone='UTC',
            enable_utc=True,
            task_routes={
                'adapters.celery.tasks.*': {'queue': 'event_manager'}
            },
            task_default_queue='event_manager',
            task_queues=[
                Queue('event_manager', routing_key='event_manager'),
                Queue('user_events', routing_key='user_events'),
                Queue('payment_events', routing_key='payment_events'),
                Queue('notification_events', routing_key='notification_events'),
            ]
        )
        
        # Register signal handlers
        @worker_ready.connect
        def worker_ready_handler(sender=None, **kwargs):
            logger.info("Celery worker ready")
        
        @worker_shutdown.connect
        def worker_shutdown_handler(sender=None, **kwargs):
            logger.info("Celery worker shutting down")
    
    async def start(self) -> None:
        """Start Celery worker"""
        logger.info("Celery adapter started (worker should be started separately)")
    
    async def stop(self) -> None:
        """Stop Celery worker"""
        if self.celery_app:
            self.celery_app.control.shutdown()
        logger.info("Celery adapter stopped")
    
    def enqueue_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        queue: str = "event_manager"
    ) -> str:
        """Enqueue event for processing"""
        from adapters.celery.tasks import process_event_task
        
        task = process_event_task.apply_async(
            args=[event_type.value, data, correlation_id, metadata],
            queue=queue
        )
        
        logger.info(f"Enqueued event {event_type.value} with task ID: {task.id}")
        return task.id
    
    def get_celery_app(self) -> Celery:
        """Get Celery application instance"""
        return self.celery_app