# adapters/inbound/http/routers/health.py
from fastapi import APIRouter
from datetime import datetime

from ..serializers import APIResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=APIResponse)
async def health_check():
    """Health check endpoint"""
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "service": "FastAPI Hexagonal",
            "version": "1.0.0"
        },
        message="Service is healthy"
    )


@router.get("/ready", response_model=APIResponse)
async def readiness_check():
    """Readiness check endpoint"""
    # Here you would check dependencies like database, external services, etc.
    return APIResponse(
        success=True,
        data={
            "status": "ready",
            "checks": {
                "database": "ok",
                "message_broker": "ok",
                "external_services": "ok"
            }
        },
        message="Service is ready"
    )
