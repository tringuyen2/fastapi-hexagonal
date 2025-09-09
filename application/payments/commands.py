# application/payments/commands.py (Fix Pydantic v2)
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class ProcessPaymentCommand(BaseModel):
    """Command to process a payment"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user_123",
                "amount": "99.99",
                "currency": "USD",
                "payment_method": "credit_card",
                "reference": "order_456"
            }
        }
    )
    
    user_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0, max_digits=10, decimal_places=2)
    currency: str = Field(..., pattern=r'^[A-Z]{3}$')
    payment_method: str = Field(..., min_length=1)
    reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None


class RefundPaymentCommand(BaseModel):
    """Command to refund a payment"""
    payment_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1)
    correlation_id: Optional[str] = None