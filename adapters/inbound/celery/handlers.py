# adapters/inbound/celery/handlers.py
from typing import Dict, Any

from core.registry import BaseHandler
from core.di.container import container
from application.users.handlers import UserCommandHandler
from application.users.commands import CreateUserCommand
from application.payments.handlers import PaymentCommandHandler
from application.payments.commands import ProcessPaymentCommand


class CeleryUserHandler(BaseHandler):
    """Celery handler for user operations"""
    
    @property
    def handler_name(self) -> str:
        return "CeleryUserHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle user Celery tasks"""
        correlation_id = context.get("correlation_id") if context else None
        
        # Get user command handler from DI container
        user_handler = container.get(UserCommandHandler)
        
        command = CreateUserCommand(
            **data,
            correlation_id=correlation_id
        )
        
        return await user_handler.handle_create_user(command)


class CeleryPaymentHandler(BaseHandler):
    """Celery handler for payment operations"""
    
    @property
    def handler_name(self) -> str:
        return "CeleryPaymentHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle payment Celery tasks"""
        correlation_id = context.get("correlation_id") if context else None
        
        # Get payment command handler from DI container  
        payment_handler = container.get(PaymentCommandHandler)
        
        command = ProcessPaymentCommand(
            **data,
            correlation_id=correlation_id
        )
        
        return await payment_handler.handle_process_payment(command)