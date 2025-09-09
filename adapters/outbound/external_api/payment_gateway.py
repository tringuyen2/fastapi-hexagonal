# adapters/outbound/external_api/payment_gateway.py
from typing import Optional, Dict, Any
from decimal import Decimal
import asyncio
import httpx
import uuid
import random
from loguru import logger

from core.exceptions import ExternalServiceException


class PaymentGatewayAdapter:
    """Payment gateway adapter for external payment processors"""
    
    def __init__(self, api_key: str, gateway_url: str):
        self.api_key = api_key
        self.gateway_url = gateway_url
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.gateway_url,
            timeout=60.0,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def process_payment(
        self,
        amount: Decimal,
        currency: str,
        payment_method: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process payment via external gateway"""
        try:
            payload = {
                "amount": str(amount),
                "currency": currency,
                "payment_method": payment_method,
                "reference": reference or f"ref_{uuid.uuid4().hex[:8]}"
            }
            
            # Mock implementation for demo
            if self.api_key == "mock_key":
                return await self._mock_process_payment(payload)
            
            # Real implementation would make HTTP request
            async with self.client or httpx.AsyncClient() as client:
                response = await client.post(
                    "/v1/payments",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Payment processed: {result.get('transaction_id')}")
                
                return {
                    "success": result.get("status") == "completed",
                    "transaction_id": result.get("transaction_id"),
                    "status": result.get("status"),
                    "error": result.get("error_message")
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Payment gateway HTTP error: {e}")
            raise ExternalServiceException("PaymentGateway", str(e))
        except Exception as e:
            logger.error(f"Payment gateway error: {e}")
            raise ExternalServiceException("PaymentGateway", str(e))
    
    async def _mock_process_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock payment processing for testing"""
        # Simulate processing delay
        await asyncio.sleep(0.2)
        
        # Simulate random failures (10% chance)
        if random.random() < 0.1:
            return {
                "success": False,
                "status": "failed",
                "error": "Insufficient funds"
            }
        
        transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
        logger.info(f"Mock payment processed: {transaction_id} for {payload['amount']} {payload['currency']}")
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": "completed"
        }