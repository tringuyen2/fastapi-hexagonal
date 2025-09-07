from typing import Dict, Type, Optional, Any
import importlib
import pkgutil
from pathlib import Path

from handlers.base import BaseHandler
from core.models import EventType
from core.exceptions import HandlerNotFoundException
from core.dependency_injection import container


class HandlerRegistry:
    """Registry for managing event handlers"""
    
    def __init__(self):
        self._handlers: Dict[EventType, Type[BaseHandler]] = {}
        self._handler_configs: Dict[EventType, Dict[str, Any]] = {}
    
    def register_handler(
        self, 
        event_type: EventType, 
        handler_class: Type[BaseHandler],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a handler for an event type"""
        self._handlers[event_type] = handler_class
        self._handler_configs[event_type] = config or {}
        
        # Register handler in DI container
        container.register_transient(handler_class, handler_class)
    
    def get_handler(self, event_type: EventType) -> BaseHandler:
        """Get handler instance for event type"""
        if event_type not in self._handlers:
            raise HandlerNotFoundException(event_type.value)
        
        handler_class = self._handlers[event_type]
        return container.get(handler_class)
    
    def get_handler_config(self, event_type: EventType) -> Dict[str, Any]:
        """Get configuration for handler"""
        return self._handler_configs.get(event_type, {})
    
    def list_handlers(self) -> Dict[EventType, Type[BaseHandler]]:
        """List all registered handlers"""
        return self._handlers.copy()
    
    def auto_discover_handlers(self, handlers_package: str = "handlers") -> None:
        """Auto-discover handlers from handlers package"""
        try:
            # Import the handlers package
            handlers_module = importlib.import_module(handlers_package)
            handlers_path = Path(handlers_module.__file__).parent
            
            # Walk through all modules in handlers package
            for _, module_name, _ in pkgutil.walk_packages([str(handlers_path)]):
                full_module_name = f"{handlers_package}.{module_name}"
                
                try:
                    module = importlib.import_module(full_module_name)
                    
                    # Find handler classes in module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseHandler) and 
                            attr != BaseHandler):
                            
                            # Try to determine event type from handler
                            event_type = self._get_event_type_from_handler(attr)
                            if event_type:
                                self.register_handler(event_type, attr)
                                
                except ImportError as e:
                    logger.warning(f"Could not import handler module {full_module_name}: {e}")
                    
        except ImportError as e:
            logger.error(f"Could not import handlers package {handlers_package}: {e}")
    
    def _get_event_type_from_handler(self, handler_class: Type[BaseHandler]) -> Optional[EventType]:
        """Try to determine event type from handler class"""
        # Check if handler has EVENT_TYPE class attribute
        if hasattr(handler_class, 'EVENT_TYPE'):
            return handler_class.EVENT_TYPE
        
        # Try to infer from class name
        class_name = handler_class.__name__.lower()
        
        if 'createuser' in class_name or 'usercreate' in class_name:
            return EventType.USER_CREATE
        elif 'updateuser' in class_name or 'userupdate' in class_name:
            return EventType.USER_UPDATE
        elif 'processpayment' in class_name or 'paymentprocess' in class_name:
            return EventType.PAYMENT_PROCESS
        elif 'sendemail' in class_name or 'notification' in class_name:
            return EventType.NOTIFICATION_SEND
        
        return None


# Global registry instance
registry = HandlerRegistry()