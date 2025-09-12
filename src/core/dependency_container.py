"""
Dependency injection container for ProxyAPI.

Provides a lightweight dependency injection system that integrates
with the existing core infrastructure.
"""

from typing import Any, Callable, Dict, TypeVar

T = TypeVar('T')


class DependencyError(Exception):
    """Raised when dependency injection fails."""


class DependencyContainer:
    """
    Lightweight dependency injection container that integrates with existing services.
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        
    def register(self, name: str, service: Any = None, factory: Callable = None, 
                 singleton: bool = True):
        """Register a service in the container."""
        if service is not None:
            if singleton:
                self._singletons[name] = service
            else:
                self._services[name] = service
        elif factory is not None:
            if singleton:
                self._factories[name] = factory
            else:
                self._services[name] = factory
    
    def get(self, name: str) -> Any:
        """Get a service from the container."""
        if name in self._singletons:
            return self._singletons[name]
            
        if name in self._services:
            service = self._services[name]
            if callable(service):
                return service()
            return service
            
        if name in self._factories:
            factory = self._factories[name]
            instance = factory()
            self._singletons[name] = instance
            del self._factories[name]
            return instance
        
        raise DependencyError(f"Service '{name}' not found")
    
    def has_service(self, name: str) -> bool:
        """Check if a service is registered."""
        return (name in self._singletons or 
               name in self._services or 
               name in self._factories)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        services = {}
        services.update(self._singletons)
        services.update(self._services)
        return services


# Global container instance
container = DependencyContainer()