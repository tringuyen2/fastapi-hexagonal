from typing import Dict, Any
from pydantic import ValidationError

from handlers.base import BaseHandler
from core.models import EventMessage, HandlerResult, EventType, UserCreateData
from services.database.interfaces import IUserRepository, INotificationRepository
from services.messaging.event_publisher import EventPublisher


class CreateUserHandler(BaseHandler):
    """Enhanced User creation handler with database persistence"""
    
    EVENT_TYPE = EventType.USER_CREATE
    
    def __init__(self, 
                 user_repository: IUserRepository, 
                 notification_repository: INotificationRepository,
                 event_publisher: EventPublisher):
        super().__init__()
        self.user_repository = user_repository
        self.notification_repository = notification_repository
        self.event_publisher = event_publisher
    
    async def handle(self, event: EventMessage) -> HandlerResult:
        """Handle user creation with database persistence"""
        try:
            # Validate and parse user data
            user_data = UserCreateData(**event.data)
            
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(user_data.email)
            if existing_user:
                return self._create_failure_result(
                    f"User with email {user_data.email} already exists",
                    "USER_ALREADY_EXISTS"
                )
            
            # Create user in database
            user_id = await self.user_repository.create_user(
                name=user_data.name,
                email=user_data.email,
                age=user_data.age,
                metadata=user_data.metadata
            )
            
            # Create welcome notification
            try:
                await self.notification_repository.create_notification(
                    recipient=user_data.email,
                    subject="Welcome to Event Manager!",
                    body=f"Hello {user_data.name}, welcome to our platform!",
                    channel="email",
                    status="pending",
                    metadata={"user_id": user_id, "type": "welcome"}
                )
            except Exception as e:
                logger.warning(f"Failed to create welcome notification: {e}")
            
            # Publish user created event
            await self.event_publisher.publish_event(
                event_type="user.created",
                data={
                    "user_id": user_id,
                    "email": user_data.email,
                    "name": user_data.name
                },
                correlation_id=event.correlation_id
            )
            
            return self._create_success_result(
                message="User created successfully",
                data={
                    "user_id": user_id,
                    "email": user_data.email,
                    "name": user_data.name
                }
            )
            
        except ValidationError as e:
            return self._create_failure_result(
                f"Invalid user data: {e}",
                "VALIDATION_ERROR"
            )
        except Exception as e:
            return self._create_failure_result(
                f"Failed to create user: {e}",
                "USER_CREATION_ERROR"
            )