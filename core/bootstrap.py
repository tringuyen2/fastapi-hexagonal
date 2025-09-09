# core/bootstrap.py
"""Application bootstrap and initialization"""
import asyncio
from typing import List
from loguru import logger

from config.settings import get_settings
from .di.bindings import binder
from .registry import registry, HandlerType


class ApplicationBootstrap:
    """Handles application initialization"""
    
    def __init__(self):
        self.settings = get_settings()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the application"""
        if self._initialized:
            return
        
        logger.info("Initializing application...")
        
        # Setup logging
        self._setup_logging()
        
        # Bind dependencies
        await binder.bind_dependencies()
        
        # Register handlers
        self._register_handlers()
        
        self._initialized = True
        logger.info("Application initialized successfully")
    
    def _setup_logging(self) -> None:
        """Setup application logging"""
        # Remove default handler
        logger.remove()
        
        # Add console handler
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=self.settings.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            colorize=True
        )
        
        # Add file handler for production
        if not self.settings.debug:
            logger.add(
                "logs/application.log",
                rotation="100 MB",
                retention="30 days",
                level=self.settings.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
            )
        
        logger.info(f"Logging configured (level: {self.settings.log_level})")
    
    def _register_handlers(self) -> None:
        """Register handlers in registry"""
        logger.debug("Registering handlers...")
        
        # Import handler classes
        from adapters.inbound.http.handlers import (
            HTTPUserHandler,
            HTTPPaymentHandler,
            HTTPNotificationHandler
        )
        from adapters.inbound.kafka.handlers import (
            KafkaUserHandler,
            KafkaPaymentHandler
        )
        from adapters.inbound.celery.handlers import (
            CeleryUserHandler,
            CeleryPaymentHandler
        )
        
        # Register user handlers
        registry.register_handler("create_user", HandlerType.HTTP, HTTPUserHandler)
        registry.register_handler("create_user", HandlerType.KAFKA, KafkaUserHandler) 
        registry.register_handler("create_user", HandlerType.CELERY, CeleryUserHandler)
        
        # Register payment handlers
        registry.register_handler("process_payment", HandlerType.HTTP, HTTPPaymentHandler)
        registry.register_handler("process_payment", HandlerType.KAFKA, KafkaPaymentHandler)
        registry.register_handler("process_payment", HandlerType.CELERY, CeleryPaymentHandler)
        
        # Register notification handlers
        registry.register_handler("send_notification", HandlerType.HTTP, HTTPNotificationHandler)
        
        logger.debug("Handlers registered")
    
    async def shutdown(self) -> None:
        """Shutdown the application"""
        logger.info("Shutting down application...")
        
        # Cleanup resources
        # This would include closing database connections, 
        # message broker connections, etc.
        
        logger.info("Application shutdown complete")


# Global bootstrap instance
bootstrap = ApplicationBootstrap()


# Convenience functions
async def initialize_application() -> None:
    """Initialize the application"""
    await bootstrap.initialize()


async def shutdown_application() -> None:
    """Shutdown the application"""
    await bootstrap.shutdown()
    