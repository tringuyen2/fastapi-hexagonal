# adapters/inbound/http/routers/payments.py
from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from core.registry import registry, HandlerType
from ..serializers import APIResponse, ProcessPaymentRequest

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=APIResponse)
async def process_payment(request: ProcessPaymentRequest, http_request: Request):
    """Process a payment"""
    try:
        # Get handler from registry
        handler = registry.get_handler("process_payment", HandlerType.HTTP)
        
        # Prepare context
        context = {
            "operation": "process",
            "request_id": getattr(http_request.state, "request_id", None)
        }
        
        # Execute handler
        result = await handler.handle(request.dict(), context)
        
        if result["success"]:
            return APIResponse(
                success=True,
                data=result["data"],
                execution_time_ms=result.get("execution_time_ms")
            )
        else:
            return APIResponse(
                success=False,
                error_code=result.get("error_code"),
                message=result.get("message")
            )
            
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
