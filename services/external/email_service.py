from typing import Optional, Dict, Any
import asyncio
import random
from dataclasses import dataclass


@dataclass
class EmailResult:
    """Email sending result"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailService:
    """Email service (Mock implementation)"""
    
    def __init__(self):
        self.sent_emails = {}
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        template_id: Optional[str] = None,
        variables: Dict[str, Any] = None
    ) -> EmailResult:
        """Send email (mock implementation)"""
        
        # Simulate sending time
        await asyncio.sleep(0.1)
        
        # Simulate random failures (5% failure rate)
        if random.random() < 0.05:
            return EmailResult(
                success=False,
                error="SMTP server temporarily unavailable"
            )
        
        # Generate message ID
        message_id = f"msg_{random.randint(100000, 999999)}"
        
        # Process template if provided
        final_body = body
        if template_id and variables:
            final_body = self._process_template(body, variables)
        
        # Store email record
        self.sent_emails[message_id] = {
            "to": to,
            "subject": subject,
            "body": final_body,
            "template_id": template_id,
            "sent_at": asyncio.get_event_loop().time()
        }
        
        return EmailResult(
            success=True,
            message_id=message_id
        )
    
    def _process_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Simple template processing"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        return result