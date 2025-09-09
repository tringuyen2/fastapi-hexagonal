# core/di/container.py
from typing import Dict, Any, Type, TypeVar, Optional, Callable, get_type_hints
from abc import ABC, abstractmethod
import inspect
from loguru import logger

T = TypeVar('T')


class DIContainer:
    """Dependency Injection Container"""
    
    def __init__(self):
        self._singletons: Dict[str, Any] = {}
        self._transients: Dict[str, Type] = {}
        self._factories: Dict[str, Callable] = {}
        self._instances: Dict[str, Any] = {}
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """Register singleton instance"""
        key = self._get_key(interface)
        self._singletons[key] = instance
        logger.debug(f"Registered singleton: {key}")
    
    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """Register transient type (new instance each time)"""
        key = self._get_key(interface)
        self._transients[key] = implementation
        logger.debug(f"Registered transient: {key} -> {implementation.__name__}")
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register factory function"""
        key = self._get_key(interface)
        self._factories[key] = factory
        logger.debug(f"Registered factory: {key}")
    
    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register specific instance (alias for singleton)"""
        self.register_singleton(interface, instance)
    
    def get(self, interface: Type[T]) -> T:
        """Get instance of type"""
        key = self._get_key(interface)
        
        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]
        
        # Check factories
        if key in self._factories:
            return self._factories[key]()
        
        # Check transients
        if key in self._transients:
            implementation_class = self._transients[key]
            return self._create_instance(implementation_class)
        
        # Try to create instance directly if it's a concrete class
        if inspect.isclass(interface) and not inspect.isabstract(interface):
            try:
                return self._create_instance(interface)
            except Exception as e:
                logger.error(f"Failed to auto-create instance of {interface}: {e}")
        
        raise ValueError(f"No registration found for {interface}")
    
    def resolve(self, interface: Type[T]) -> T:
        """Alias for get method"""
        return self.get(interface)
    
    def is_registered(self, interface: Type[T]) -> bool:
        """Check if type is registered"""
        key = self._get_key(interface)
        return key in self._singletons or key in self._transients or key in self._factories
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._singletons.clear()
        self._transients.clear()
        self._factories.clear()
        self._instances.clear()
        logger.debug("Container cleared")
    
    def _get_key(self, interface: Type) -> str:
        """Get registration key for type"""
        return f"{interface.__module__}.{interface.__name__}"
    
    def _create_instance(self, cls: Type[T]) -> T:
        """Create instance with dependency injection"""
        try:
            # Get constructor signature
            signature = inspect.signature(cls.__init__)
            kwargs = {}
            
            # Get type hints for better dependency resolution
            type_hints = get_type_hints(cls.__init__)
            
            for param_name, param in signature.parameters.items():
                if param_name == 'self':
                    continue
                
                # Try to resolve from type hints first
                param_type = type_hints.get(param_name, param.annotation)
                
                if param_type != param.empty:
                    try:
                        kwargs[param_name] = self.get(param_type)
                    except ValueError:
                        # If dependency not found and no default value, raise error
                        if param.default == param.empty:
                            logger.error(f"Cannot resolve dependency {param_type} for {cls.__name__}.{param_name}")
                            raise ValueError(f"Cannot resolve dependency {param_type} for {cls.__name__}")
                        # Otherwise, use default value (by not setting in kwargs)
            
            instance = cls(**kwargs)
            logger.debug(f"Created instance of {cls.__name__} with dependencies: {list(kwargs.keys())}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create instance of {cls}: {e}")
            raise


# Global container instance
container = DIContainer()