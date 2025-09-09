# adapters/inbound/celery/worker.py
from celery import Celery
from celery.signals import worker_ready, worker_shutdown
from kombu import Queue
from loguru import logger

from config.settings import get_settings
from core.bootstrap import initialize_application, shutdown_application


def create_celery_app() -> Celery:
    """Create Celery application"""
    settings = get_settings()
    
    celery_app = Celery(
        'fastapi-hexagonal',
        broker=settings.redis.url,
        backend=settings.redis.url
    )
    
    # Configure Celery
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_routes={
            'adapters.inbound.celery.tasks.*': {'queue': 'default'}
        },
        task_default_queue='default',
        task_queues=[
            Queue('default', routing_key='default'),
            Queue('users', routing_key='users'),
            Queue('payments', routing_key='payments'),
        ],
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True
    )
    
    return celery_app


celery_app = create_celery_app()


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Worker ready signal handler"""
    logger.info("Celery worker is ready")
    # Initialize application when worker starts
    import asyncio
    asyncio.run(initialize_application())


@worker_shutdown.connect  
def worker_shutdown_handler(sender=None, **kwargs):
    """Worker shutdown signal handler"""
    logger.info("Celery worker shutting down")
    # Cleanup when worker shuts down
    import asyncio
    asyncio.run(shutdown_application())