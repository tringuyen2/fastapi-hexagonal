from typing import Dict, Any, Type, TypeVar, Optional
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')


class DIContainer:
    """Simple Dependency Injection Container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton service"""
        key = self._get_key(interface)
        self._singletons[key] = implementation
    
    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Register a factory for service creation"""
        key = self._get_key(interface)
        self._factories[key] = factory
    
    def register_transient(self, interface: Type[T], implementation_class: Type[T]) -> None:
        """Register a transient service (new instance each time)"""
        key = self._get_key(interface)
        self._services[key] = implementation_class
    
    def get(self, interface: Type[T]) -> T:
        """Get service instance"""
        key = self._get_key(interface)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            return self._factories[key]()
        
        # Check transient services
        if key in self._services:
            service_class = self._services[key]
            return self._create_instance(service_class)
        
        raise ValueError(f"Service {interface} not registered")
    
    def _get_key(self, interface: Type) -> str:
        """Get key for service registration"""
        return f"{interface.__module__}.{interface.__name__}"
    
    def _create_instance(self, service_class: Type[T]) -> T:
        """Create instance with dependency injection"""
        # Get constructor signature
        signature = inspect.signature(service_class.__init__)
        kwargs = {}
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
            
            if param.annotation != param.empty:
                try:
                    kwargs[param_name] = self.get(param.annotation)
                except ValueError:
                    # If dependency not found and no default value, raise error
                    if param.default == param.empty:
                        raise ValueError(f"Cannot resolve dependency {param.annotation} for {service_class}")
        
        return service_class(**kwargs)


# Global DI container instance
container = DIContainer()