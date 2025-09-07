import asyncio
import signal
import sys
from typing import List, Optional
from contextlib import asynccontextmanager
import argparse

from loguru import logger
from core.config import load_config
from core.registry import registry
from core.dependency_injection import container
from adapters.http.adapter import HTTPAdapter
from adapters.celery.adapter import CeleryAdapter
from adapters.kafka.adapter import KafkaAdapter

# Import database factory
from services.database.factory import DatabaseFactory, DatabaseType
from services.database.interfaces import IUserRepository, IPaymentRepository, INotificationRepository

# Import external services
from services.external.email_service import EmailService
from services.external.payment_gateway import PaymentGateway
from services.messaging.event_publisher import EventPublisher

# Import handlers for registration
from handlers.user.create_user import CreateUserHandler
from handlers.payment.process_payment import ProcessPaymentHandler
from handlers.notification.send_email import SendEmailHandler


class EventManagerApp:
    """Main Event Manager Application with Database Support"""
    
    def __init__(self, database_type: DatabaseType = DatabaseType.SQLITE):
        self.config = load_config()
        self.database_type = database_type
        self.adapters: List = []
        self.running = False
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logger.remove()
        logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>"
        )
        
        # Add file logging in production
        if not self.config.debug:
            logger.add(
                "logs/event_manager.log",
                rotation="100 MB",
                retention="7 days",
                level=self.config.log_level
            )
    
    async def _setup_database_repositories(self):
        """Setup database repositories based on configuration"""
        
        # Get database configuration
        db_config = self._get_database_config()
        
        try:
            # Create repositories
            user_repository = await DatabaseFactory.create_user_repository(
                self.database_type, db_config
            )
            payment_repository = await DatabaseFactory.create_payment_repository(
                self.database_type, db_config
            )
            notification_repository = await DatabaseFactory.create_notification_repository(
                self.database_type, db_config
            )
            
            # Register in DI container
            container.register_singleton(IUserRepository, user_repository)
            container.register_singleton(IPaymentRepository, payment_repository)
            container.register_singleton(INotificationRepository, notification_repository)
            
            logger.info(f"Initialized {self.database_type.value} repositories")
            
        except Exception as e:
            logger.error(f"Failed to setup database repositories: {e}")
            raise
    
    def _get_database_config(self) -> dict:
        """Get database configuration based on type"""
        
        if self.database_type == DatabaseType.MONGODB:
            return {
                "connection_string": getattr(self.config, 'mongodb_url', "mongodb://localhost:27017"),
                "database_name": getattr(self.config, 'mongodb_database', "event_manager")
            }
        elif self.database_type == DatabaseType.POSTGRESQL:
            return {
                "host": getattr(self.config, 'pg_host', "localhost"),
                "port": getattr(self.config, 'pg_port', 5432),
                "database": getattr(self.config, 'pg_database', "event_manager"),
                "username": getattr(self.config, 'pg_username', "postgres"),
                "password": getattr(self.config, 'pg_password', "postgres")
            }
        else:
            return {}  # SQLite doesn't need config
    
    async def _setup_dependencies(self):
        """Setup dependency injection container"""
        
        # Setup database repositories first
        await self._setup_database_repositories()
        
        # Register external services
        container.register_singleton(EmailService, EmailService())
        container.register_singleton(PaymentGateway, PaymentGateway())
        container.register_singleton(EventPublisher, EventPublisher())
        
        logger.info("Dependency injection container configured")
    
    def _register_handlers(self):
        """Register event handlers"""
        # Register handlers with their event types
        from core.models import EventType
        
        registry.register_handler(EventType.USER_CREATE, CreateUserHandler)
        registry.register_handler(EventType.PAYMENT_PROCESS, ProcessPaymentHandler)
        registry.register_handler(EventType.NOTIFICATION_SEND, SendEmailHandler)
        
        logger.info(f"Registered {len(registry.list_handlers())} handlers")
    
    async def start_adapters(self, adapter_types: List[str]):
        """Start specified adapters"""
        for adapter_type in adapter_types:
            if adapter_type == "http":
                adapter = HTTPAdapter()
                await adapter.start()
                self.adapters.append(adapter)
                
            elif adapter_type == "celery":
                adapter = CeleryAdapter()
                await adapter.start()
                self.adapters.append(adapter)
                
            elif adapter_type == "kafka":
                adapter = KafkaAdapter()
                await adapter.start()
                self.adapters.append(adapter)
                
            else:
                logger.warning(f"Unknown adapter type: {adapter_type}")
    
    async def stop_adapters(self):
        """Stop all adapters"""
        for adapter in self.adapters:
            try:
                await adapter.stop()
            except Exception as e:
                logger.error(f"Error stopping adapter {adapter.adapter_name}: {e}")
        
        self.adapters.clear()
    
    async def initialize(self):
        """Initialize the application"""
        try:
            logger.info(f"Initializing Event Manager with {self.database_type.value} database")
            
            # Setup dependencies and handlers
            await self._setup_dependencies()
            self._register_handlers()
            
            logger.info("Event Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def run(self, adapter_types: List[str]):
        """Run the application with specified adapters"""
        try:
            # Initialize application
            await self.initialize()
            
            logger.info(f"Starting Event Manager with adapters: {', '.join(adapter_types)}")
            
            # Start adapters
            await self.start_adapters(adapter_types)
            
            self.running = True
            
            # Setup signal handlers for graceful shutdown
            def signal_handler(sig, frame):
                logger.info(f"Received signal {sig}, shutting down...")
                self.running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Special case for HTTP-only mode
            if adapter_types == ["http"]:
                http_adapter = next(a for a in self.adapters if isinstance(a, HTTPAdapter))
                http_adapter.run(
                    host="0.0.0.0",
                    port=8000,
                    debug=self.config.debug
                )
            else:
                # For other adapters, keep the main thread alive
                while self.running:
                    await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
            raise
        finally:
            await self.stop_adapters()
            logger.info("Event Manager stopped")


def main():
    """Enhanced main entry point with database support"""
    parser = argparse.ArgumentParser(description="Event Manager - Hexagonal Architecture")
    parser.add_argument(
        "--adapters",
        nargs="+",
        choices=["http", "celery", "kafka"],
        default=["http"],
        help="Adapters to start (default: http)"
    )
    parser.add_argument(
        "--database",
        choices=["sqlite", "mongodb", "postgresql"],
        default="sqlite",
        help="Database type to use (default: sqlite)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Determine database type
    db_type = DatabaseType(args.database)
    
    # Create and run application
    app = EventManagerApp(database_type=db_type)
    
    # Override debug mode if specified
    if args.debug:
        app.config.debug = True
        app.config.log_level = "DEBUG"
    
    try:
        asyncio.run(app.run(args.adapters))
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()