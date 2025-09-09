# application/payments/use_cases.py (Fixed imports)
from typing import Protocol, Optional
from abc import abstractmethod
import uuid
from decimal import Decimal

from domain.payments.entities import Payment, PaymentStatus
from domain.payments.value_objects import PaymentId, TransactionId, Money, PaymentMethod
from domain.users.value_objects import UserId
from domain.users.services import UserDomainService
from .commands import ProcessPaymentCommand, RefundPaymentCommand
from core.exceptions import NotFoundError, BusinessRuleViolationError


class PaymentRepository(Protocol):
    """Payment repository port"""
    
    @abstractmethod
    async def create(self, payment: Payment) -> None:
        pass
    
    @abstractmethod
    async def get_by_id(self, payment_id: PaymentId) -> Optional[Payment]:
        pass
    
    @abstractmethod
    async def update(self, payment: Payment) -> None:
        pass


class PaymentGateway(Protocol):
    """Payment gateway port"""
    
    @abstractmethod
    async def process_payment(
        self, 
        amount: Decimal, 
        currency: str, 
        payment_method: str,
        reference: Optional[str] = None
    ) -> dict:
        pass


class EventPublisher(Protocol):
    """Event publisher port"""
    
    @abstractmethod
    async def publish(self, event_type: str, data: dict, correlation_id: Optional[str] = None) -> None:
        pass


class ProcessPaymentUseCase:
    """Use case for processing payments"""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        payment_gateway: PaymentGateway,
        user_domain_service: UserDomainService,
        event_publisher: EventPublisher
    ):
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.user_domain_service = user_domain_service
        self.event_publisher = event_publisher
    
    async def execute(self, command: ProcessPaymentCommand) -> Payment:
        """Execute process payment use case"""
        # Validate user exists
        user_id = UserId(command.user_id)
        await self.user_domain_service.ensure_user_exists(user_id)
        
        # Create payment entity
        payment = Payment(
            payment_id=PaymentId(str(uuid.uuid4())),
            user_id=user_id,
            money=Money(command.amount, command.currency),
            payment_method=PaymentMethod(command.payment_method),
            reference=command.reference,
            metadata=command.metadata
        )
        
        # Persist payment
        await self.payment_repository.create(payment)
        
        # Mark as processing
        payment.mark_as_processing()
        await self.payment_repository.update(payment)
        
        try:
            # Process through external gateway
            result = await self.payment_gateway.process_payment(
                amount=command.amount,
                currency=command.currency,
                payment_method=command.payment_method,
                reference=command.reference
            )
            
            if result["success"]:
                # Mark as completed
                payment.mark_as_completed(TransactionId(result["transaction_id"]))
                await self.payment_repository.update(payment)
                
                # Publish success event
                await self.event_publisher.publish(
                    event_type="payment.completed",
                    data={
                        "payment_id": str(payment.payment_id),
                        "user_id": str(user_id),
                        "amount": str(command.amount),
                        "currency": command.currency,
                        "transaction_id": result["transaction_id"]
                    },
                    correlation_id=command.correlation_id
                )
            else:
                # Mark as failed
                payment.mark_as_failed(result.get("error", "Payment processing failed"))
                await self.payment_repository.update(payment)
                
                # Publish failure event
                await self.event_publisher.publish(
                    event_type="payment.failed",
                    data={
                        "payment_id": str(payment.payment_id),
                        "user_id": str(user_id),
                        "reason": payment.failure_reason
                    },
                    correlation_id=command.correlation_id
                )
                
        except Exception as e:
            # Mark as failed on exception
            payment.mark_as_failed(f"Gateway error: {str(e)}")
            await self.payment_repository.update(payment)
            raise
        
        return payment
