from typing import Dict, Any
from pydantic import ValidationError

from handlers.base import BaseHandler
from core.models import EventMessage, HandlerResult, EventType, NotificationData
from services.external.email_service import EmailService


class SendEmailHandler(BaseHandler):
    """Handler for email notification events"""
    
    EVENT_TYPE = EventType.NOTIFICATION_SEND
    
    def __init__(self, email_service: EmailService):
        super().__init__()
        self.email_service = email_service
    
    async def handle(self, event: EventMessage) -> HandlerResult:
        """Handle email notification"""
        try:
            # Validate and parse notification data
            notification_data = NotificationData(**event.data)
            
            # Only handle email notifications
            if notification_data.channel != "email":
                return self._create_failure_result(
                    f"This handler only supports email channel, got: {notification_data.channel}",
                    "UNSUPPORTED_CHANNEL"
                )
            
            # Send email
            result = await self.email_service.send_email(
                to=notification_data.recipient,
                subject=notification_data.subject,
                body=notification_data.body,
                template_id=notification_data.template_id,
                variables=notification_data.variables
            )
            
            if result.success:
                return self._create_success_result(
                    message="Email sent successfully",
                    data={"message_id": result.message_id}
                )
            else:
                return self._create_failure_result(
                    f"Failed to send email: {result.error}",
                    "EMAIL_SEND_FAILED"
                )
                
        except ValidationError as e:
            return self._create_failure_result(
                f"Invalid notification data: {e}",
                "VALIDATION_ERROR"
            )
        except Exception as e:
            return self._create_failure_result(
                f"Failed to send email notification: {e}",
                "EMAIL_NOTIFICATION_ERROR"
            )