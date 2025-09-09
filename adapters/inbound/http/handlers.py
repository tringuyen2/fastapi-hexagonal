# adapters/inbound/http/handlers.py
from typing import Dict, Any
from fastapi import Request

from core.registry import BaseHandler
from core.di.container import container
from application.users.handlers import UserCommandHandler
from application.users.commands import CreateUserCommand, UpdateUserCommand, DeleteUserCommand
from application.payments.handlers import PaymentCommandHandler  
from application.payments.commands import ProcessPaymentCommand
from application.notifications.handlers import NotificationCommandHandler
from application.notifications.commands import SendNotificationCommand


class HTTPUserHandler(BaseHandler):
    """HTTP handler for user operations"""
    
    @property
    def handler_name(self) -> str:
        return "HTTPUserHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle user HTTP requests"""
        operation = context.get("operation") if context else None
        request_id = context.get("request_id") if context else None
        
        # Get user command handler from DI container
        user_handler = container.get(UserCommandHandler)
        
        if operation == "create":
            command = CreateUserCommand(
                **data,
                correlation_id=request_id
            )
            return await user_handler.handle_create_user(command)
            
        elif operation == "update":
            user_id = context.get("user_id")
            command = UpdateUserCommand(
                user_id=user_id,
                **data,
                correlation_id=request_id
            )
            return await user_handler.handle_update_user(command)
            
        elif operation == "delete":
            user_id = context.get("user_id")
            command = DeleteUserCommand(
                user_id=user_id,
                correlation_id=request_id
            )
            return await user_handler.handle_delete_user(command)
            
        else:
            return {
                "success": False,
                "error_code": "INVALID_OPERATION",
                "message": f"Unknown operation: {operation}"
            }


class HTTPPaymentHandler(BaseHandler):
    """HTTP handler for payment operations"""
    
    @property
    def handler_name(self) -> str:
        return "HTTPPaymentHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle payment HTTP requests"""
        operation = context.get("operation", "process") if context else "process"
        request_id = context.get("request_id") if context else None
        
        # Get payment command handler from DI container
        payment_handler = container.get(PaymentCommandHandler)
        
        if operation == "process":
            command = ProcessPaymentCommand(
                **data,
                correlation_id=request_id
            )
            return await payment_handler.handle_process_payment(command)
        else:
            return {
                "success": False,
                "error_code": "INVALID_OPERATION",
                "message": f"Unknown operation: {operation}"
            }


class HTTPNotificationHandler(BaseHandler):
    """HTTP handler for notification operations"""
    
    @property
    def handler_name(self) -> str:
        return "HTTPNotificationHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle notification HTTP requests"""
        operation = context.get("operation", "send") if context else "send"
        request_id = context.get("request_id") if context else None
        
        # Get notification command handler from DI container
        notification_handler = container.get(NotificationCommandHandler)
        
        if operation == "send":
            command = SendNotificationCommand(
                **data,
                correlation_id=request_id
            )
            return await notification_handler.handle_send_notification(command)
        else:
            return {
                "success": False,
                "error_code": "INVALID_OPERATION", 
                "message": f"Unknown operation: {operation}"
            }
