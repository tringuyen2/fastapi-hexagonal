from typing import Dict, Any
from pydantic import ValidationError
from datetime import datetime

from handlers.base import BaseHandler
from core.models import EventMessage, HandlerResult, EventType, PaymentProcessData
from services.external.payment_gateway import PaymentGateway
from services.database.interfaces import IUserRepository, IPaymentRepository, INotificationRepository
from services.messaging.event_publisher import EventPublisher


class ProcessPaymentHandler(BaseHandler):
    """Enhanced Payment processing handler with database persistence"""
    
    EVENT_TYPE = EventType.PAYMENT_PROCESS
    
    def __init__(
        self, 
        payment_gateway: PaymentGateway, 
        user_repository: IUserRepository,
        payment_repository: IPaymentRepository,
        notification_repository: INotificationRepository,
        event_publisher: EventPublisher
    ):
        super().__init__()
        self.payment_gateway = payment_gateway
        self.user_repository = user_repository
        self.payment_repository = payment_repository
        self.notification_repository = notification_repository
        self.event_publisher = event_publisher
    
    async def handle(self, event: EventMessage) -> HandlerResult:
        """Handle payment processing with database persistence"""
        try:
            # Validate and parse payment data
            payment_data = PaymentProcessData(**event.data)
            
            # Validate user exists
            user = await self.user_repository.get_by_id(payment_data.user_id)
            if not user:
                return self._create_failure_result(
                    f"User {payment_data.user_id} not found",
                    "USER_NOT_FOUND"
                )
            
            # Process payment through external gateway
            payment_result = await self.payment_gateway.process_payment(
                amount=payment_data.amount,
                currency=payment_data.currency,
                payment_method=payment_data.payment_method,
                user_id=payment_data.user_id,
                reference=payment_data.reference
            )
            
            # Store payment record regardless of success/failure
            payment_record_id = await self.payment_repository.create_payment(
                user_id=payment_data.user_id,
                amount=payment_data.amount,
                currency=payment_data.currency,
                transaction_id=payment_result.transaction_id or f"failed_{datetime.utcnow().timestamp()}",
                status=payment_result.status,
                metadata={
                    "payment_method": payment_data.payment_method,
                    "reference": payment_data.reference,
                    "gateway_response": {
                        "success": payment_result.success,
                        "error_message": payment_result.error_message
                    }
                }
            )
            
            if payment_result.success:
                # Create success notification
                try:
                    await self.notification_repository.create_notification(
                        recipient=user["email"],
                        subject="Payment Successful",
                        body=f"Your payment of {payment_data.amount} {payment_data.currency} has been processed successfully.",
                        channel="email",
                        status="pending",
                        metadata={
                            "user_id": payment_data.user_id,
                            "transaction_id": payment_result.transaction_id,
                            "type": "payment_success"
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to create payment success notification: {e}")
                
                # Publish payment success event
                await self.event_publisher.publish_event(
                    event_type="payment.completed",
                    data={
                        "user_id": payment_data.user_id,
                        "amount": payment_data.amount,
                        "currency": payment_data.currency,
                        "transaction_id": payment_result.transaction_id,
                        "payment_record_id": payment_record_id
                    },
                    correlation_id=event.correlation_id
                )
                
                return self._create_success_result(
                    message="Payment processed successfully",
                    data={
                        "transaction_id": payment_result.transaction_id,
                        "payment_record_id": payment_record_id,
                        "status": payment_result.status
                    }
                )
            else:
                # Create failure notification
                try:
                    await self.notification_repository.create_notification(
                        recipient=user["email"],
                        subject="Payment Failed",
                        body=f"Your payment of {payment_data.amount} {payment_data.currency} could not be processed: {payment_result.error_message}",
                        channel="email",
                        status="pending",
                        metadata={
                            "user_id": payment_data.user_id,
                            "type": "payment_failure",
                            "error": payment_result.error_message
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to create payment failure notification: {e}")
                
                return self._create_failure_result(
                    f"Payment failed: {payment_result.error_message}",
                    "PAYMENT_FAILED"
                )
                
        except ValidationError as e:
            return self._create_failure_result(
                f"Invalid payment data: {e}",
                "VALIDATION_ERROR"
            )
        except Exception as e:
            return self._create_failure_result(
                f"Failed to process payment: {e}",
                "PAYMENT_PROCESSING_ERROR"
            )