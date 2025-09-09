# application/notifications/handlers.py
from typing import Dict, Any
import time
from loguru import logger

from .use_cases import SendNotificationUseCase
from .commands import SendNotificationCommand
from core.exceptions import DomainException, ApplicationException


class NotificationCommandHandler:
    """Handler for notification commands"""
    
    def __init__(self, send_notification_use_case: SendNotificationUseCase):
        self.send_notification_use_case = send_notification_use_case
    
    async def handle_send_notification(self, command: SendNotificationCommand) -> Dict[str, Any]:
        """Handle send notification command"""
        start_time = time.time()
        
        try:
            logger.info(f"Sending notification to: {command.recipient}")
            
            notification = await self.send_notification_use_case.execute(command)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Notification processed: {notification.notification_id} in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "data": notification.to_dict(),
                "execution_time_ms": execution_time
            }
            
        except DomainException as e:
            execution_time = (time.time() - start_time) * 1000
            logger.warning(f"Domain error sending notification: {e.message}")
            
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error sending notification: {e}")
            
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "execution_time_ms": execution_time
            }