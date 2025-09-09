# adapters/inbound/kafka/handlers.py
from typing import Dict, Any

from core.registry import BaseHandler
from core.di.container import container
from application.users.handlers import UserCommandHandler
from application.users.commands import CreateUserCommand
from application.payments.handlers import PaymentCommandHandler
from application.payments.commands import ProcessPaymentCommand


class KafkaUserHandler(BaseHandler):
    """Kafka handler for user operations"""
    
    @property
    def handler_name(self) -> str:
        return "KafkaUserHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle user Kafka messages"""
        correlation_id = context.get("correlation_id") if context else None
        
        # Get user command handler from DI container
        user_handler = container.get(UserCommandHandler)
        
        # For Kafka, we primarily handle create operations
        # The message structure determines the operation type
        command = CreateUserCommand(
            **data,
            correlation_id=correlation_id
        )
        
        return await user_handler.handle_create_user(command)


class KafkaPaymentHandler(BaseHandler):
    """Kafka handler for payment operations"""
    
    @property
    def handler_name(self) -> str:
        return "KafkaPaymentHandler"
    
    async def handle(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle payment Kafka messages"""
        correlation_id = context.get("correlation_id") if context else None
        
        # Get payment command handler from DI container
        payment_handler = container.get(PaymentCommandHandler)
        
        command = ProcessPaymentCommand(
            **data,
            correlation_id=correlation_id
        )
        
        return await payment_handler.handle_process_payment(command)
