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
from .controllers.config_controller import router as config_router
from .controllers.health_controller import router as health_router
from .controllers.context_controller import router as context_router
from src.core.rate_limiter import rate_limiter
from .errors.custom_exceptions import APIException, ProviderNotFoundError, ProviderUnavailableError
from .errors.error_handlers import (global_exception_handler,
                                    http_exception_handler,
                                    validation_exception_handler)
from .validation.middleware import middleware_pipeline
from fastapi import APIRouter, Depends, HTTPException, Request
from src.core.provider_factory import provider_factory
from src.core.circuit_breaker import get_circuit_breaker
from src.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

# Create main API router
main_router = APIRouter(prefix="/v1")

# --- Dynamic Endpoints ---

@main_router.get("/models", tags=["models"])
async def list_models():
    """OpenAI-compatible /v1/models endpoint to list all 100+ models from the registry."""
    return {
        "object": "list",
        "data": await provider_factory.list_all_models()
    }

@main_router.post("/chat/completions", tags=["chat"])
async def chat_completions(request: Request):
    """
    Main dynamic routing endpoint for chat completions.
    Routes requests to the appropriate provider based on the 'model' field.
    """
    body = await request.json()
    model_name = body.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="'model' field is required.")

    with logger.span("dynamic_chat_completions", attributes={"model": model_name}):
        try:
            client, config = await provider_factory.get_provider_client(model_name)
            breaker = get_circuit_breaker(config.provider)

            # Use the circuit breaker to make the call
            response = await breaker.call(
                client.chat_completions,
                model=model_name,
                messages=body.get("messages", []),
                **{k: v for k, v in body.items() if k not in ["model", "messages"]}
            )

            # Log spend if pricing info is available
            pricing = provider_factory.get_pricing(model_name)
            if pricing and response.get("usage"):
                input_tokens = response["usage"].get("prompt_tokens", 0)
                output_tokens = response["usage"].get("completion_tokens", 0)
                cost = (input_tokens * pricing["input"] / 1000) + (output_tokens * pricing["output"] / 1000)
                logger.info(f"Request cost estimated: ${cost:.6f}", model=model_name)

            return response

        except ProviderNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ProviderUnavailableError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            logger.error("An unexpected error occurred during chat completion", error=str(e))
            raise HTTPException(status_code=500, detail="An internal server error occurred.")

@main_router.post("/embeddings", tags=["embeddings"])
async def embeddings(request: Request):
    """Dynamic routing endpoint for embeddings."""
    body = await request.json()
    model_name = body.get("model")
    if not model_name:
        raise HTTPException(status_code=400, detail="'model' field is required.")

    with logger.span("dynamic_embeddings", attributes={"model": model_name}):
        try:
            client, config = await provider_factory.get_provider_client(model_name)
            breaker = get_circuit_breaker(config.provider)

            response = await breaker.call(
                client.embeddings,
                model=model_name,
                input=body.get("input", []),
                **{k: v for k, v in body.items() if k not in ["model", "input"]}
            )
            return response
        except ProviderNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ProviderUnavailableError as e:
            raise HTTPException(status_code=503, detail=str(e))
        except Exception as e:
            logger.error("An unexpected error occurred during embeddings", error=str(e))
            raise HTTPException(status_code=500, detail="An internal server error occurred.")

# Include other controller routers that are not being replaced
main_router.include_router(health_router, tags=["health"])
main_router.include_router(context_router, tags=["context"])
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