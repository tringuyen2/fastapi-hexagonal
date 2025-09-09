# core/di/bindings.py (Fixed for graceful degradation)
from typing import Dict, Any
import asyncio
from loguru import logger

from .container import container
from config.settings import get_settings

# Import domain services
from domain.users.services import UserDomainService, UserRepository

# Import use cases with correct protocols
from application.users.use_cases import (
    CreateUserUseCase, UpdateUserUseCase, DeleteUserUseCase,
    NotificationRepository as UserNotificationRepository,
    EventPublisher as UserEventPublisher
)
from application.payments.use_cases import (
    ProcessPaymentUseCase,
    PaymentRepository, PaymentGateway,
    EventPublisher as PaymentEventPublisher
)
from application.notifications.use_cases import (
    SendNotificationUseCase,
    NotificationRepository, EmailService,
    EventPublisher as NotificationEventPublisher
)

# Import handlers
from application.users.handlers import UserCommandHandler
from application.payments.handlers import PaymentCommandHandler
from application.notifications.handlers import NotificationCommandHandler


class MockEventPublisher:
    """Mock event publisher for when Kafka is not available"""
    
    async def publish(self, event_type: str, data: dict, correlation_id: str = None) -> None:
        """Mock publish - just log the event"""
        logger.info(f"Mock Event Published: {event_type} - {data}")


class DependencyBinder:
    """Handles dependency injection bindings with graceful degradation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.kafka_available = False
        self.redis_available = False
    
    async def bind_dependencies(self) -> None:
        """Bind all dependencies in container"""
        logger.info("Binding dependencies...")
        
        # Bind configurations
        container.register_singleton(type(self.settings), self.settings)
        
        # Bind outbound adapters (infrastructure)
        await self._bind_repositories()
        await self._bind_external_services()
        await self._bind_message_broker()
        
        # Bind domain services
        self._bind_domain_services()
        
        # Bind use cases
        self._bind_use_cases()
        
        # Bind application handlers
        self._bind_handlers()
        
        logger.info("Dependencies bound successfully")
    
    async def _bind_repositories(self) -> None:
        """Bind repository implementations"""
        logger.debug("Binding repositories...")
        
        # Database type selection based on configuration
        db_type = self.settings.database.type
        
        if db_type == "postgresql":
            try:
                # Import and initialize PostgreSQL repositories
                from adapters.outbound.db.postgresql.adapter import PostgreSQLAdapter
                from adapters.outbound.db.postgresql.repositories import (
                    PostgreSQLUserRepository,
                    PostgreSQLPaymentRepository,
                    PostgreSQLNotificationRepository
                )
                
                # Create database adapter
                db_adapter = PostgreSQLAdapter(self.settings.database)
                await db_adapter.connect()
                
                # Register repositories
                user_repo = PostgreSQLUserRepository(db_adapter)
                payment_repo = PostgreSQLPaymentRepository(db_adapter)
                notification_repo = PostgreSQLNotificationRepository(db_adapter)
                
                logger.debug("Using PostgreSQL repositories")
                
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}, falling back to in-memory")
                user_repo, payment_repo, notification_repo = self._get_memory_repositories()
                
        elif db_type == "mongodb":
            try:
                # Import and initialize MongoDB repositories
                from adapters.outbound.db.mongodb.adapter import MongoDBAdapter
                from adapters.outbound.db.mongodb.repositories import (
                    MongoUserRepository,
                    MongoPaymentRepository,
                    MongoNotificationRepository
                )
                
                # Create database adapter
                db_adapter = MongoDBAdapter(self.settings.database)
                await db_adapter.connect()
                
                # Register repositories
                user_repo = MongoUserRepository(db_adapter)
                payment_repo = MongoPaymentRepository(db_adapter)
                notification_repo = MongoNotificationRepository(db_adapter)
                
                logger.debug("Using MongoDB repositories")
                
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}, falling back to in-memory")
                user_repo, payment_repo, notification_repo = self._get_memory_repositories()
                
        else:  # sqlite or in-memory
            user_repo, payment_repo, notification_repo = self._get_memory_repositories()
            logger.debug("Using in-memory repositories")
        
        # Register in container using protocol types
        container.register_singleton(UserRepository, user_repo)
        container.register_singleton(PaymentRepository, payment_repo)
        container.register_singleton(NotificationRepository, notification_repo)
        
        # Also register for different use case interfaces
        container.register_singleton(UserNotificationRepository, notification_repo)
        
        logger.debug(f"Bound {db_type} repositories")
    
    def _get_memory_repositories(self):
        """Get in-memory repositories"""
        from adapters.outbound.db.memory.repositories import (
            MemoryUserRepository,
            MemoryPaymentRepository,
            MemoryNotificationRepository
        )
        
        return (
            MemoryUserRepository(),
            MemoryPaymentRepository(),
            MemoryNotificationRepository()
        )
    
    async def _bind_external_services(self) -> None:
        """Bind external service adapters"""
        logger.debug("Binding external services...")
        
        # Email service
        from adapters.outbound.external_api.email_service import EmailServiceAdapter
        email_adapter = EmailServiceAdapter(
            api_key=self.settings.email_service_api_key
        )
        
        # Payment gateway
        from adapters.outbound.external_api.payment_gateway import PaymentGatewayAdapter
        payment_adapter = PaymentGatewayAdapter(
            api_key=self.settings.payment_gateway_api_key,
            gateway_url=self.settings.payment_gateway_url
        )
        
        # Register using protocol types
        container.register_singleton(EmailService, email_adapter)
        container.register_singleton(PaymentGateway, payment_adapter)
        
        logger.debug("Bound external services")
    
    async def _bind_message_broker(self) -> None:
        """Bind message broker adapters with graceful degradation"""
        logger.debug("Binding message broker...")
        
        event_publisher = None
        
        # Try to connect to Kafka and Redis
        try:
            from adapters.outbound.message_broker.event_publisher import EventPublisherAdapter
            event_publisher = EventPublisherAdapter(
                kafka_config=self.settings.kafka,
                redis_config=self.settings.redis
            )
            await event_publisher.connect()
            self.kafka_available = True
            self.redis_available = True
            logger.info("Connected to Kafka and Redis for event publishing")
            
        except Exception as e:
            logger.warning(f"Message broker connection failed: {e}")
            
            # Try Redis only
            try:
                from adapters.outbound.message_broker.redis_publisher import RedisPublisherAdapter
                redis_publisher = RedisPublisherAdapter(self.settings.redis)
                await redis_publisher.connect()
                
                # Create a wrapper that only uses Redis
                class RedisOnlyEventPublisher:
                    def __init__(self, redis_pub):
                        self.redis_publisher = redis_pub
                    
                    async def publish(self, event_type: str, data: dict, correlation_id: str = None) -> None:
                        await self.redis_publisher.publish_event(
                            channel=f"events.{event_type}",
                            event_type=event_type,
                            data=data,
                            correlation_id=correlation_id
                        )
                
                event_publisher = RedisOnlyEventPublisher(redis_publisher)
                self.redis_available = True
                logger.info("Connected to Redis for event publishing (Kafka unavailable)")
                
            except Exception as redis_e:
                logger.warning(f"Redis connection also failed: {redis_e}")
                
                # Fall back to mock publisher
                event_publisher = MockEventPublisher()
                logger.info("Using mock event publisher (no message broker available)")
        
        # Register using protocol types for all use cases
        container.register_singleton(UserEventPublisher, event_publisher)
        container.register_singleton(PaymentEventPublisher, event_publisher)
        container.register_singleton(NotificationEventPublisher, event_publisher)
        
        logger.debug("Bound message broker")
    
    def _bind_domain_services(self) -> None:
        """Bind domain services"""
        logger.debug("Binding domain services...")
        
        # User domain service
        container.register_transient(UserDomainService, UserDomainService)
        
        logger.debug("Bound domain services")
    
    def _bind_use_cases(self) -> None:
        """Bind use cases"""
        logger.debug("Binding use cases...")
        
        # User use cases
        container.register_transient(CreateUserUseCase, CreateUserUseCase)
        container.register_transient(UpdateUserUseCase, UpdateUserUseCase)
        container.register_transient(DeleteUserUseCase, DeleteUserUseCase)
        
        # Payment use cases
        container.register_transient(ProcessPaymentUseCase, ProcessPaymentUseCase)
        
        # Notification use cases
        container.register_transient(SendNotificationUseCase, SendNotificationUseCase)
        
        logger.debug("Bound use cases")
    
    def _bind_handlers(self) -> None:
        """Bind application handlers"""
        logger.debug("Binding handlers...")
        
        # User command handler
        container.register_transient(UserCommandHandler, UserCommandHandler)
        container.register_transient(PaymentCommandHandler, PaymentCommandHandler)
        container.register_transient(NotificationCommandHandler, NotificationCommandHandler)
        
        logger.debug("Bound handlers")


# Global binder instance
binder = DependencyBinder()