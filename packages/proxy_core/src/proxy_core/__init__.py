"""
Proxy Core - Core routing and resilience components for LLM Proxy.

This package provides essential components for:
- Circuit breaker pattern implementation
- Rate limiting strategies
- HTTP client optimization
- Provider lifecycle management
"""

__version__ = "1.0.0"
__author__ = "ProxyAPI Team"
__email__ = "team@proxyapi.dev"

from .circuit_breaker import (
    CircuitBreaker,
    ProductionCircuitBreaker,
    CircuitBreakerOpenException,
    CircuitState,
    get_circuit_breaker,
    reset_all_circuit_breakers,
)
from .rate_limiter import RateLimiter
from .http_client import OptimizedHTTPClient, get_http_client
from .provider_factory import ProviderFactory, BaseProvider, ProviderStatus
from .models import ProviderConfig, ProviderType, ModelInfo
from .logging import ContextualLogger
from .metrics import metrics_collector
from .config import config_manager

__all__ = [
    "CircuitBreaker",
    "ProductionCircuitBreaker",
    "CircuitBreakerOpenException",
    "CircuitState",
    "get_circuit_breaker",
    "reset_all_circuit_breakers",
    "RateLimiter",
    "OptimizedHTTPClient",
    "get_http_client",
    "ProviderFactory",
    "BaseProvider",
    "ProviderStatus",
    "ProviderConfig",
    "ProviderType",
    "ModelInfo",
    "ContextualLogger",
    "metrics_collector",
    "config_manager",
]