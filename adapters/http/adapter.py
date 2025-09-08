# adapters/http/adapter.py
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from adapters.base_adapter import BaseAdapter
from adapters.http.serializers import (
    HTTPEventRequest, 
    HTTPEventResponse, 
    HealthCheckResponse
)
from adapters.http.middleware import RequestLoggingMiddleware
from core.models import EventType
from core.config import load_config
from loguru import logger


class HTTPAdapter(BaseAdapter):
    """HTTP adapter using FastAPI"""
    
    def __init__(self):
        super().__init__("http")
        self.app = None
        self.config = load_config()
        self.server = None
    
    async def start(self) -> None:
        """Start HTTP server"""
        self.app = self._create_app()
        logger.info("HTTP adapter started")
    
    async def stop(self) -> None:
        """Stop HTTP server"""
        logger.info("HTTP adapter stopped")
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            logger.info("FastAPI application starting...")
            yield
            # Shutdown
            logger.info("FastAPI application shutting down...")
        
        app = FastAPI(
            title="Event Manager HTTP API",
            description="HTTP adapter for Event Manager using Hexagonal Architecture",
            version="1.0.0",
            lifespan=lifespan
        )
        
        # Add middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        app.add_middleware(RequestLoggingMiddleware)
        
        # Add routes
        self._add_routes(app)
        
        return app
    
    def _add_routes(self, app: FastAPI) -> None:
        """Add API routes"""
        
        @app.get("/health", response_model=HealthCheckResponse)
        async def health_check():
            """Health check endpoint"""
            return HealthCheckResponse(
                status="healthy",
                adapters={"http": "running"}
            )
        
        @app.post("/events", response_model=HTTPEventResponse)
        async def process_event(request: HTTPEventRequest):
            """Process event endpoint"""
            try:
                result = await self.process_event(
                    event_type=request.event_type,
                    data=request.data,
                    correlation_id=request.correlation_id,
                    metadata=request.metadata
                )
                
                return HTTPEventResponse.from_handler_result(result)
                
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {str(e)}"
                )
        
        # Convenience endpoints for specific event types
        @app.post("/users", response_model=HTTPEventResponse)
        async def create_user(request: Dict[str, Any]):
            """Create user convenience endpoint"""
            return await process_event(HTTPEventRequest(
                event_type=EventType.USER_CREATE,
                data=request
            ))
        
        @app.post("/payments", response_model=HTTPEventResponse)
        async def process_payment(request: Dict[str, Any]):
            """Process payment convenience endpoint"""
            return await process_event(HTTPEventRequest(
                event_type=EventType.PAYMENT_PROCESS,
                data=request
            ))
        
        @app.post("/notifications", response_model=HTTPEventResponse)
        async def send_notification(request: Dict[str, Any]):
            """Send notification convenience endpoint"""
            return await process_event(HTTPEventRequest(
                event_type=EventType.NOTIFICATION_SEND,
                data=request
            ))
    
    # def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
    #     """Run the HTTP server"""
    #     if not self.app:
    #         self.app = self._create_app()
        
    #     uvicorn.run(
    #         self.app,
    #         host=host,
    #         port=port,
    #         log_level="debug" if debug else "info",
    #         reload=debug
    #     )

    async def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Start HTTP server"""
        self.app = self._create_app()
        logger.info(f"Starting HTTP server on {host}:{port}")
        
        config = uvicorn.Config(
            self.app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
            reload=debug
        )
        self.server = uvicorn.Server(config)
        logger.info("HTTP adapter started")
        await self.server.serve()