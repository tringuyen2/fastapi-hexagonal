# application/users/use_cases.py (Fixed imports)
from typing import Protocol, Optional
from abc import abstractmethod
import uuid
from datetime import datetime

from domain.users.entities import User
from domain.users.value_objects import UserId, UserName, Email, Age
from domain.users.services import UserRepository, UserDomainService
from domain.notifications.entities import Notification
from domain.notifications.value_objects import (
    NotificationId, Recipient, NotificationContent, NotificationChannel
)
from .commands import CreateUserCommand, UpdateUserCommand, DeleteUserCommand
from core.exceptions import NotFoundError, AlreadyExistsError


class NotificationRepository(Protocol):
    """Notification repository port"""
    
    @abstractmethod
    async def create(self, notification: Notification) -> None:
        pass


class EventPublisher(Protocol):
    """Event publisher port"""
    
    @abstractmethod
    async def publish(self, event_type: str, data: dict, correlation_id: Optional[str] = None) -> None:
        pass


# Rest of the use cases remain the same...
class CreateUserUseCase:
    """Use case for creating a user"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService,
        notification_repository: NotificationRepository,
        event_publisher: EventPublisher
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
        self.notification_repository = notification_repository
        self.event_publisher = event_publisher
    
    async def execute(self, command: CreateUserCommand) -> User:
        """Execute create user use case"""
        # Create domain objects
        user_id = UserId(str(uuid.uuid4()))
        name = UserName(command.name)
        email = Email(command.email)
        age = Age(command.age) if command.age is not None else None
        
        # Check business rules
        await self.user_domain_service.ensure_unique_email(email)
        
        # Create user entity
        user = User(
            user_id=user_id,
            name=name,
            email=email,
            age=age,
            metadata=command.metadata
        )
        
        # Persist user
        await self.user_repository.create(user)
        
        # Create welcome notification
        welcome_notification = Notification(
            notification_id=NotificationId(str(uuid.uuid4())),
            recipient=Recipient(str(email), NotificationChannel.EMAIL),
            content=NotificationContent(
                subject="Welcome to FastAPI Hexagonal!",
                body=f"Hello {name}, welcome to our platform!",
            ),
            user_id=user_id,
            metadata={"type": "welcome"}
        )
        await self.notification_repository.create(welcome_notification)
        
        # Publish domain event
        await self.event_publisher.publish(
            event_type="user.created",
            data={
                "user_id": str(user_id),
                "name": str(name),
                "email": str(email)
            },
            correlation_id=command.correlation_id
        )
        
        return user


class UpdateUserUseCase:
    """Use case for updating a user"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService,
        event_publisher: EventPublisher
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
        self.event_publisher = event_publisher
    
    async def execute(self, command: UpdateUserCommand) -> User:
        """Execute update user use case"""
        user_id = UserId(command.user_id)
        
        # Get existing user
        user = await self.user_domain_service.ensure_user_exists(user_id)
        
        # Update fields
        if command.name:
            user.update_name(UserName(command.name))
        
        if command.age is not None:
            user.update_age(Age(command.age))
        
        if command.metadata is not None:
            for key, value in command.metadata.items():
                user.add_metadata(key, value)
        
        # Persist changes
        await self.user_repository.update(user)
        
        # Publish domain event
        await self.event_publisher.publish(
            event_type="user.updated",
            data={
                "user_id": str(user_id),
                "changes": {
                    "name": command.name,
                    "age": command.age,
                    "metadata": command.metadata
                }
            },
            correlation_id=command.correlation_id
        )
        
        return user


class DeleteUserUseCase:
    """Use case for deleting a user"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService,
        event_publisher: EventPublisher
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
        self.event_publisher = event_publisher
    
    async def execute(self, command: DeleteUserCommand) -> None:
        """Execute delete user use case"""
        user_id = UserId(command.user_id)
        
        # Ensure user exists
        user = await self.user_domain_service.ensure_user_exists(user_id)
        
        # Delete user
        await self.user_repository.delete(user_id)
        
        # Publish domain event
        await self.event_publisher.publish(
            event_type="user.deleted",
            data={
                "user_id": str(user_id),
                "email": str(user.email)
            },
            correlation_id=command.correlation_id
        )