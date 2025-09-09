# core/registry.py
from typing import Dict, Any, Type, Optional, Callable
from abc import ABC, abstractmethod
from enum import Enum
import importlib
from loguru import logger

from .di.container import container


class HandlerType(Enum):
    """Handler type enumeration"""
    HTTP = "http"
    KAFKA = "kafka" 
    CELERY = "celery"


class BaseHandler(ABC):
    """Base handler interface"""
    
    @property
    @abstractmethod
    def handler_name(self) -> str:
        """Handler name"""
        pass
    
    @abstractmethod
    async def handle(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle request"""
        pass


class HandlerRegistry:
    """Registry for managing handlers across different adapters"""
    
    def __init__(self):
        self._handlers: Dict[str, Dict[HandlerType, Type[BaseHandler]]] = {}
        self._handler_configs: Dict[str, Dict[str, Any]] = {}
    
    def register_handler(
        self,
        operation: str,
        handler_type: HandlerType,
        handler_class: Type[BaseHandler],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register handler for operation and adapter type"""
        if operation not in self._handlers:
            self._handlers[operation] = {}
        
        self._handlers[operation][handler_type] = handler_class
        
        # Store configuration
        config_key = f"{operation}.{handler_type.value}"
        self._handler_configs[config_key] = config or {}
        
        logger.debug(f"Registered handler: {operation}.{handler_type.value} -> {handler_class.__name__}")
    
    def get_handler(self, operation: str, handler_type: HandlerType) -> BaseHandler:
        """Get handler instance for operation and type"""
        if operation not in self._handlers:
            raise ValueError(f"No handlers registered for operation: {operation}")
        
        if handler_type not in self._handlers[operation]:
            raise ValueError(f"No {handler_type.value} handler registered for operation: {operation}")
        
        handler_class = self._handlers[operation][handler_type]
        
        # Create instance using DI container
        return container.get(handler_class)
    
    def get_handler_config(self, operation: str, handler_type: HandlerType) -> Dict[str, Any]:
        """Get handler configuration"""
        config_key = f"{operation}.{handler_type.value}"
        return self._handler_configs.get(config_key, {})
    
    def list_operations(self) -> Dict[str, list]:
        """List all registered operations and their handler types"""
        result = {}
        for operation, handlers in self._handlers.items():
            result[operation] = list(handlers.keys())
        return result
    
    def auto_discover_handlers(self, package_name: str) -> None:
        """Auto-discover handlers from package"""
        try:
            package = importlib.import_module(package_name)
            logger.debug(f"Auto-discovering handlers in {package_name}")
            
            # This would implement handler discovery logic
            # For now, we'll rely on manual registration
            
        except ImportError as e:
            logger.warning(f"Could not import package {package_name}: {e}")


# Global registry instance
registry = HandlerRegistry()