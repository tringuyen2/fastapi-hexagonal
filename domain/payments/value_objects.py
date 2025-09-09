# domain/payments/value_objects.py
from typing import Optional
from dataclasses import dataclass
from decimal import Decimal
import re

from core.exceptions import ValidationError


@dataclass(frozen=True)
class PaymentId:
    """Payment ID value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("Payment ID cannot be empty", "payment_id")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TransactionId:
    """Transaction ID value object"""
    value: str
    
    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValidationError("Transaction ID cannot be empty", "transaction_id")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Money:
    """Money value object"""
    amount: Decimal
    currency: str
    
    def __post_init__(self):
        if self.amount <= 0:
            raise ValidationError("Amount must be positive", "amount")
        
        # Validate currency format (ISO 4217)
        if not re.match(r'^[A-Z]{3}$', self.currency):
            raise ValidationError("Currency must be 3-letter ISO code", "currency")
    
    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
    
    def add(self, other: "Money") -> "Money":
        """Add money (same currency only)"""
        if self.currency != other.currency:
            raise ValidationError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)


@dataclass(frozen=True)
class PaymentMethod:
    """Payment method value object"""
    type: str  # credit_card, debit_card, paypal, etc.
    details: Optional[str] = None
    
    def __post_init__(self):
        valid_types = ["credit_card", "debit_card", "paypal", "bank_transfer"]
        if self.type not in valid_types:
            raise ValidationError(f"Invalid payment method: {self.type}", "payment_method")
    
    def __str__(self) -> str:
        return self.type