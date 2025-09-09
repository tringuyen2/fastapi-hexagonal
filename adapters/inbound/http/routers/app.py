# adapters/inbound/http/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config.settings import get_settings
from core.bootstrap import initialize_application, shutdown_application
from .middleware import RequestLoggingMiddleware
from .routers import users_router, payments_router, notifications_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting FastAPI application...")
    await initialize_application()
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    await shutdown_application()


def create_app() -> FastAPI:
    """Create FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="FastAPI Hexagonal Architecture",
        description="A FastAPI application built with Hexagonal Architecture principles",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add middleware
    if settings.debug:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add routers
    app.include_router(health_router)
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(payments_router, prefix="/api/v1")
    app.include_router(notifications_router, prefix="/api/v1")
    
    return app