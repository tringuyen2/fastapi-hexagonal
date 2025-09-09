# adapters/inbound/http/routers/__init__.py
from .users import router as users_router
from .payments import router as payments_router
from .notifications import router as notifications_router
from .health import router as health_router

__all__ = ["users_router", "payments_router", "notifications_router", "health_router"]