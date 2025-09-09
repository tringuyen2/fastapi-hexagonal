# adapters/outbound/external_api/email_service.py
from typing import Optional, Dict, Any
import asyncio
import httpx
from loguru import logger

from core.exceptions import ExternalServiceException


class EmailServiceAdapter:
    """Email service adapter for external email providers"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.emailservice.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email via external service"""
        try:
            payload = {
                "to": recipient,
                "subject": subject,
                "body": body
            }
            
            if template_id:
                payload["template_id"] = template_id
                payload["variables"] = variables or {}
            
            # Mock implementation for demo
            if self.api_key == "mock_key":
                return await self._mock_send_email(payload)
            
            # Real implementation would make HTTP request
            async with self.client or httpx.AsyncClient() as client:
                response = await client.post(
                    "/v1/emails",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Email sent successfully: {result.get('message_id')}")
                
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "status": "sent"
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Email service HTTP error: {e}")
            raise ExternalServiceException("EmailService", str(e))
        except Exception as e:
            logger.error(f"Email service error: {e}")
            raise ExternalServiceException("EmailService", str(e))
    
    async def _mock_send_email(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Mock email sending for testing"""
        import uuid
        import random
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Simulate random failures (5% chance)
        if random.random() < 0.05:
            raise ExternalServiceException("EmailService", "Service temporarily unavailable")
        
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock email sent to {payload['to']}: {message_id}")
        
        return {
            "success": True,
            "message_id": message_id,
            "status": "sent"
        }
