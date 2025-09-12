"""
Proxy API - FastAPI and validation components for LLM Proxy.

This package provides:
- FastAPI application setup and configuration
- Request/response validation schemas
- API endpoints for proxy operations
- Authentication and authorization
"""

__version__ = "1.0.0"
__author__ = "ProxyAPI Team"
__email__ = "team@proxyapi.dev"

from .app import create_app
from .schemas import (
    ChatRequest,
    ChatResponse,
    ModelInfo,
    ModelsResponse,
    HealthCheck,
)
from .endpoints import router as api_router
from .models import (
    ModelSelectionRequest,
    ModelListResponse,
    ModelDetailResponse,
    RefreshResponse,
    ModelInfoExtended,
    ProviderConfig
)
from .exceptions import (
    ProxyAPIException,
    InvalidRequestError,
    NotFoundError,
    AuthenticationError,
    RateLimitError
)
from .auth import verify_api_key, get_api_key_from_request
from .rate_limiter import rate_limiter

__all__ = [
    "create_app",
    "ChatRequest",
    "ChatResponse",
    "ModelInfo",
    "ModelsResponse",
    "HealthCheck",
    "api_router",
    "ModelSelectionRequest",
    "ModelListResponse",
    "ModelDetailResponse",
    "RefreshResponse",
    "ModelInfoExtended",
    "ProviderConfig",
    "ProxyAPIException",
    "InvalidRequestError",
    "NotFoundError",
    "AuthenticationError",
    "RateLimitError",
    "verify_api_key",
    "get_api_key_from_request",
    "rate_limiter",
]