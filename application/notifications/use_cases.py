# application/notifications/use_cases.py (Fixed imports)
from typing import Protocol, Optional
from abc import abstractmethod
import uuid

from domain.notifications.entities import Notification, NotificationStatus
from domain.notifications.value_objects import (
    NotificationId, Recipient, NotificationContent, NotificationChannel
)
from domain.users.value_objects import UserId
from .commands import SendNotificationCommand
from core.exceptions import ValidationError


class NotificationRepository(Protocol):
    """Notification repository port"""
    
    @abstractmethod
    async def create(self, notification: Notification) -> None:
        pass
    
    @abstractmethod
    async def update(self, notification: Notification) -> None:
        pass


class EmailService(Protocol):
    """Email service port"""
    
    @abstractmethod
    async def send_email(
        self, 
        recipient: str, 
        subject: str, 
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[dict] = None
    ) -> dict:
        pass


class EventPublisher(Protocol):
    """Event publisher port"""
    
    @abstractmethod
    async def publish(self, event_type: str, data: dict, correlation_id: Optional[str] = None) -> None:
        pass


class SendNotificationUseCase:
    """Use case for sending notifications"""
    
    def __init__(
        self,
        notification_repository: NotificationRepository,
        email_service: EmailService,
        event_publisher: EventPublisher
    ):
        self.notification_repository = notification_repository
        self.email_service = email_service
        self.event_publisher = event_publisher
    
    async def execute(self, command: SendNotificationCommand) -> Notification:
        """Execute send notification use case"""
        # Create notification entity
        channel = NotificationChannel(command.channel)
        
        # Process template variables in body
        body = command.body
        for key, value in command.variables.items():
            body = body.replace(f"{{{key}}}", str(value))
        
        notification = Notification(
            notification_id=NotificationId(str(uuid.uuid4())),
            recipient=Recipient(command.recipient, channel),
            content=NotificationContent(
                subject=command.subject,
                body=body,
                template_id=command.template_id
            ),
            user_id=UserId(command.user_id) if command.user_id else None
        )
        
        # Persist notification
        await self.notification_repository.create(notification)
        
        try:
            # Send notification based on channel
            if channel == NotificationChannel.EMAIL:
                result = await self.email_service.send_email(
                    recipient=command.recipient,
                    subject=command.subject,
                    body=body,
                    template_id=command.template_id,
                    variables=command.variables
                )
                
                if result["success"]:
                    notification.mark_as_sent(result.get("message_id"))
                else:
                    notification.mark_as_failed(result.get("error", "Failed to send email"))
            
            else:
                # Other channels would be implemented here
                notification.mark_as_failed(f"Channel {command.channel} not implemented")
            
            # Update notification status
            await self.notification_repository.update(notification)
            
            # Publish event
            event_type = "notification.sent" if notification.status == NotificationStatus.SENT else "notification.failed"
            await self.event_publisher.publish(
                event_type=event_type,
                data={
                    "notification_id": str(notification.notification_id),
                    "recipient": command.recipient,
                    "channel": command.channel,
                    "status": notification.status.value
                },
                correlation_id=command.correlation_id
            )
            
        except Exception as e:
            # Mark as failed on exception
            notification.mark_as_failed(f"Service error: {str(e)}")
            await self.notification_repository.update(notification)
            raise
        
        return notification
