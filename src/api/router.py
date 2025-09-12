"""
API Gateway Router - Main entry point for all API endpoints.

This module creates the centralized API router that combines all controllers,
applies middleware, and handles errors consistently across the application.
"""

import time

from fastapi import APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .controllers.alerting_controller import router as alerting_router
from .controllers.analytics_controller import router as analytics_router
from .controllers.chat_controller import router as chat_router
from .controllers.config_controller import router as config_router
from .controllers.health_controller import router as health_router
from .controllers.model_controller import router as model_router
from src.core.rate_limiter import rate_limiter
from .errors.custom_exceptions import APIException
from .errors.error_handlers import (global_exception_handler,
                                    http_exception_handler,
                                    validation_exception_handler)
from .validation.middleware import middleware_pipeline

# Create main API router
main_router = APIRouter(prefix="/v1")

# Include all controller routers
main_router.include_router(chat_router, tags=["chat"])
main_router.include_router(model_router, tags=["models"])
main_router.include_router(health_router, tags=["health"])
main_router.include_router(analytics_router, tags=["analytics"])
main_router.include_router(alerting_router, tags=["alerting"])
main_router.include_router(config_router, prefix="/config", tags=["config"])

class APIGatewayMiddleware(BaseHTTPMiddleware):
    """Main API gateway middleware that orchestrates all middleware processing."""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Dispatch request through middleware pipeline."""
        return await middleware_pipeline.process_request(request, call_next)

# Middleware setup functions
def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    app.add_middleware(APIGatewayMiddleware)

def setup_exception_handlers(app):
    """Setup global exception handlers for the FastAPI application."""

    # Register exception handlers
    app.add_exception_handler(Exception, global_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(APIException, global_exception_handler)

    # Add additional handlers for common HTTP exceptions
    from fastapi import HTTPException
    app.add_exception_handler(HTTPException, http_exception_handler)

def create_api_router():
    """Create and return the main API router with all endpoints."""
    return main_router

# Health check endpoint at root level (before /v1 prefix)
root_router = APIRouter()

@root_router.get("/health")
@rate_limiter.limit(route="/health")
async def root_health_check(request: Request):
    """Basic health check at root level."""
    return {
        "status": "healthy",
        "service": "proxy-api-gateway",
        "timestamp": int(time.time())
    }

@root_router.get("/")
async def root_info():
    """Basic API information."""
    return {
        "name": "Proxy API Gateway",
        "version": "1.0.0",
        "description": "Unified API gateway for LLM proxy with intelligent routing",
        "endpoints": {
            "chat": "/v1/chat/completions",
            "models": "/v1/models",
            "health": "/v1/health",
            "analytics": "/v1/metrics",
            "alerting": "/v1/alerts",
            "monitoring": "/monitoring",
            "config": "/v1/config/reload"
        }
    }

@root_router.get("/monitoring")
async def monitoring_dashboard():
    """Serve the monitoring dashboard."""
    try:
        with open("templates/monitoring_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, status_code=200)
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Monitoring dashboard template not found"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to load monitoring dashboard: {str(e)}"}
        )

# Additional utility endpoints
@main_router.get("/status")
@rate_limiter.limit(route="/v1/status")
async def api_status(request: Request):
    """Detailed API status information."""
    return {
        "status": "operational",
        "version": "1.0.0",
        "uptime": "unknown",  # Could be enhanced with actual uptime tracking
        "timestamp": int(time.time()),
        "features": [
            "chat_completions",
            "text_completions",
            "embeddings",
            "image_generation",
            "model_discovery",
            "health_monitoring",
            "analytics"
        ]
    }

# Request/Response logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for detailed request/response logging."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url}")

        response = await call_next(request)

        # Log response
        process_time = time.time() - start_time
        print(".2f")

        return response

# CORS middleware (if needed)
class CORSMiddleware(BaseHTTPMiddleware):
    """CORS middleware for cross-origin requests."""

    def __init__(self, app, allow_origins=None):
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add CORS headers
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allow_origins)
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, X-API-Key"

        return response

# Initialize additional middleware
request_logging_middleware = RequestLoggingMiddleware(None)
cors_middleware = CORSMiddleware(None)

def setup_additional_middleware(app):
    """Setup additional utility middleware."""
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(CORSMiddleware)

# Export all necessary components
__all__ = [
    'main_router',
    'root_router',
    'create_api_router',
    'setup_middleware',
    'setup_exception_handlers',
    'setup_additional_middleware'
]