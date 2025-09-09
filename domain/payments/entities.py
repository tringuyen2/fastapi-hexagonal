# domain/payments/entities.py
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .value_objects import PaymentId, TransactionId, Money, PaymentMethod
from ..users.value_objects import UserId
from core.exceptions import BusinessRuleViolationError


class PaymentStatus(Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


@dataclass
class Payment:
    """Payment domain entity"""
    payment_id: PaymentId
    user_id: UserId
    money: Money
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    transaction_id: Optional[TransactionId] = None
    reference: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def mark_as_processing(self) -> None:
        """Mark payment as processing"""
        if self.status != PaymentStatus.PENDING:
            raise BusinessRuleViolationError(
                "Payment status transition",
                f"Cannot mark as processing from {self.status.value}"
            )
        self.status = PaymentStatus.PROCESSING
        self.updated_at = datetime.utcnow()
    
    def mark_as_completed(self, transaction_id: TransactionId) -> None:
        """Mark payment as completed"""
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise BusinessRuleViolationError(
                "Payment status transition",
                f"Cannot complete payment from {self.status.value}"
            )
        self.status = PaymentStatus.COMPLETED
        self.transaction_id = transaction_id
        self.failure_reason = None
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self, reason: str) -> None:
        """Mark payment as failed"""
        if self.status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise BusinessRuleViolationError(
                "Payment status transition",
                f"Cannot fail payment from {self.status.value}"
            )
        self.status = PaymentStatus.FAILED
        self.failure_reason = reason
        self.updated_at = datetime.utcnow()
    
    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return self.status == PaymentStatus.COMPLETED
    
    def refund(self) -> None:
        """Refund the payment"""
        if not self.can_be_refunded():
            raise BusinessRuleViolationError(
                "Payment refund",
                f"Cannot refund payment with status {self.status.value}"
            )
        self.status = PaymentStatus.REFUNDED
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "payment_id": str(self.payment_id),
            "user_id": str(self.user_id),
            "amount": float(self.money.amount),
            "currency": self.money.currency,
            "payment_method": str(self.payment_method),
            "status": self.status.value,
            "transaction_id": str(self.transaction_id) if self.transaction_id else None,
            "reference": self.reference,
            "failure_reason": self.failure_reason,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
