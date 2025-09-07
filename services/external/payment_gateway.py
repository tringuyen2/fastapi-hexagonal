from typing import Optional
import asyncio
import random
from dataclasses import dataclass


@dataclass
class PaymentResult:
    """Payment processing result"""
    success: bool
    transaction_id: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None


class PaymentGateway:
    """Payment gateway service (Mock implementation)"""
    
    def __init__(self):
        self.processed_payments = {}
    
    async def process_payment(
        self, 
        amount: float, 
        currency: str, 
        payment_method: str,
        user_id: str,
        reference: Optional[str] = None
    ) -> PaymentResult:
        """Process payment (mock implementation)"""
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Simulate random failures (10% failure rate)
        if random.random() < 0.1:
            return PaymentResult(
                success=False,
                status="failed",
                error_message="Payment declined by bank"
            )
        
        # Generate transaction ID
        transaction_id = f"txn_{random.randint(100000, 999999)}"
        
        # Store payment record
        self.processed_payments[transaction_id] = {
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "user_id": user_id,
            "reference": reference,
            "status": "completed"
        }
        
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            status="completed"
        )
    
    async def get_payment_status(self, transaction_id: str) -> Optional[dict]:
        """Get payment status"""
        await asyncio.sleep(0.05)
        return self.processed_payments.get(transaction_id)