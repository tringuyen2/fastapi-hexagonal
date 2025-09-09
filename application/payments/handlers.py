# application/payments/handlers.py
from typing import Dict, Any
import time
from loguru import logger
from decimal import Decimal

from .use_cases import ProcessPaymentUseCase
from .commands import ProcessPaymentCommand
from core.exceptions import DomainException, ApplicationException


class PaymentCommandHandler:
    """Handler for payment commands"""
    
    def __init__(self, process_payment_use_case: ProcessPaymentUseCase):
        self.process_payment_use_case = process_payment_use_case
    
    async def handle_process_payment(self, command: ProcessPaymentCommand) -> Dict[str, Any]:
        """Handle process payment command"""
        start_time = time.time()
        
        try:
            logger.info(f"Processing payment for user: {command.user_id}")
            
            payment = await self.process_payment_use_case.execute(command)
            
            execution_time = (time.time() - start_time) * 1000
            logger.info(f"Payment processed: {payment.payment_id} in {execution_time:.2f}ms")
            
            return {
                "success": True,
                "data": payment.to_dict(),
                "execution_time_ms": execution_time
            }
            
        except DomainException as e:
            execution_time = (time.time() - start_time) * 1000
            logger.warning(f"Domain error processing payment: {e.message}")
            
            return {
                "success": False,
                "error_code": e.error_code,
                "message": e.message,
                "execution_time_ms": execution_time
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Unexpected error processing payment: {e}")
            
            return {
                "success": False,
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "execution_time_ms": execution_time
            }