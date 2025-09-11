"""
LLM Proxy API - Main Application Server
High-performance proxy with intelligent routing and fallback capabilities.
"""

import asyncio
import uvicorn
import re
import json
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Union
import time
import uuid
import threading
from http import HTTPStatus
from datetime import datetime, timezone

# FastAPI imports
from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# HTTP client
import httpx

# Core imports
from src.core.config import settings
from src.core.logging import setup_logging, ContextualLogger
from src.core.unified_config import config_manager
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, APIKeyAuth
from src.core.unified_config import ProviderConfig
from src.core.exceptions import (
    ProviderError, InvalidRequestError, AuthenticationError,
    RateLimitError, ServiceUnavailableError, NotImplementedError
)
from src.models.requests import ChatCompletionRequest, TextCompletionRequest, EmbeddingRequest
from src.services.provider_loader import get_provider_factories
from src.core.circuit_breaker import get_circuit_breaker
from src.utils.context_condenser import condense_context

# Performance optimization imports
from src.core.http_client import get_http_client, initialize_http_client
from src.core.smart_cache import get_response_cache, get_summary_cache, initialize_caches, shutdown_caches
from src.core.memory_manager import get_memory_manager, initialize_memory_manager, shutdown_memory_manager

from src.core.config import settings
from src.core.logging import setup_logging, ContextualLogger
from src.core.unified_config import config_manager
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, APIKeyAuth
from src.core.unified_config import ProviderConfig
from src.core.exceptions import ProviderError, InvalidRequestError, AuthenticationError, RateLimitError, ServiceUnavailableError
from src.models.requests import ChatCompletionRequest, TextCompletionRequest, EmbeddingRequest
from src.services.provider_loader import get_provider_factories
from src.core.circuit_breaker import get_circuit_breaker
from src.utils.context_condenser import condense_context
from datetime import datetime


# Setup logging
setup_logging(
    log_level="DEBUG" if settings.debug else "INFO",
    log_file=settings.log_file
)
logger = ContextualLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


# Utility Functions
def get_provider(provider_config: ProviderConfig) -> Any:
    """Get or create provider instance with caching"""
    # This would be implemented with proper caching mechanism
    # For now, return a mock implementation
    return None


def get_providers_for_model(request: Request, model: str) -> List[ProviderConfig]:
    """Get sorted list of enabled providers that support the given model"""
    providers = [
        provider for provider in request.app.config.providers
        if provider.enabled and model in provider.models
    ]
    providers.sort(key=lambda p: p.priority)
    return providers


async def handle_context_condensation(
    request: Request,
    background_tasks: BackgroundTasks,
    req: Dict[str, Any],
    operation: str
) -> Optional[Dict[str, Any]]:
    """Handle context condensation for long requests"""
    config = request.app.state.condensation_config
    total_content = sum(len(m["content"]) for m in req.get("messages", []))

    if total_content > config.truncation_threshold:
        request_id = str(uuid.uuid4())
        full_chunks = [m["content"] for m in req["messages"]]
        background_tasks.add_task(background_condense, request_id, request, full_chunks)

        if not req.get("stream", False):
            return {
                "status": "processing",
                "request_id": request_id,
                "message": "Long context detected; summarization in progress. Poll /summary/{request_id} for result.",
                "estimated_time": "5-10 seconds"
            }

        # For streaming, truncate and proceed
        truncate_len = config.truncation_threshold // 2
        num_messages_to_keep = max(1, len(req["messages"]) * truncate_len // total_content)
        truncated_messages = req["messages"][-num_messages_to_keep:]
        req["messages"] = truncated_messages
        logger.info(f"Proactive truncation for long context ({total_content} chars), background task added: {request_id}")

    return None


async def process_request_with_fallback(
    request: Request,
    req: Dict[str, Any],
    providers: List[ProviderConfig],
    operation: str,
    background_tasks: BackgroundTasks
) -> Union[Dict[str, Any], StreamingResponse]:
    """Process request with intelligent fallback logic"""
    last_exception = None
    config = request.app.state.condensation_config

    for provider_config in providers:
        try:
            logger.info(f"Attempting {operation} with provider: {provider_config.name}")

            provider = get_provider(provider_config)
            if not provider:
                continue

            circuit_breaker = get_circuit_breaker(f"provider_{provider_config.name}")

            # Choose appropriate method
            if operation == "chat_completion":
                method = provider.create_completion
            elif operation == "text_completion":
                method = provider.create_text_completion
            elif operation == "embeddings":
                method = provider.create_embeddings
            else:
                raise ValueError(f"Unknown operation: {operation}")

            # Execute with circuit breaker
            response = await circuit_breaker.execute(lambda: method(req))

            # Handle streaming responses
            if hasattr(response, '__aiter__'):
                return StreamingResponse(response, media_type="text/event-stream")

            logger.info(f"{operation} successful", provider=provider_config.name)
            return response

        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider_config.name} failed: {e}")

            # Handle context length errors
            msg = str(e)
            if any(re.search(pattern, msg, re.IGNORECASE) for pattern in config.error_patterns):
                if not req.get("stream", False):
                    request_id = str(uuid.uuid4())
                    chunks = [m["content"] for m in req.get("messages", [])]
                    background_tasks.add_task(background_condense, request_id, request, chunks)

                    return {
                        "status": "processing",
                        "request_id": request_id,
                        "message": f"Context error detected; summarization in progress. Poll /summary/{request_id} for result.",
                        "estimated_time": "5-10 seconds"
                    }

                # Truncate for streaming
                req["messages"] = req["messages"][-len(req["messages"])//2:]
                req["stream"] = False

            continue

    # All providers failed
    logger.error(f"All providers failed for {operation}", error=str(last_exception))
    raise ServiceUnavailableError("All providers are currently unavailable")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with performance optimizations"""
    logger.info("Starting LLM Proxy API with performance optimizations")

    # Initialize configuration
    try:
        config = config_manager.load_config()
        app.state.config = config
        app.config = config
        app.state.condensation_config = config.settings.condensation

        # Initialize performance systems
        logger.info("Initializing performance optimization systems...")

        # Initialize HTTP client
        app.state.http_client = await get_http_client()
        logger.info("HTTP client initialized")

        # Initialize caches
        app.state.response_cache = await get_response_cache()
        app.state.summary_cache_obj = await get_summary_cache()
        logger.info("Smart caches initialized")

        # Initialize memory manager
        app.state.memory_manager = await get_memory_manager()
        logger.info("Memory manager initialized")

        # Legacy cache support (for backward compatibility)
        app.state.cache = {}
        app.state.summary_cache = {}

        # Initialize authentication
        api_key_auth = APIKeyAuth(settings.proxy_api_keys)
        app.state.api_key_auth = api_key_auth

        # Initialize providers
        app.state.provider_factories = get_provider_factories(config.providers)
        logger.info(f"Loaded {len(app.state.config.providers)} providers")

        app.state.config_mtime = config_manager._last_modified

        # Start web UI in background thread
        def start_web_ui():
            try:
                from web_ui import app as web_app
                logger.info("Starting web UI on port 10000")
                web_app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)
            except Exception as e:
                logger.error(f"Failed to start web UI: {e}")

        web_ui_thread = threading.Thread(target=start_web_ui, daemon=True)
        web_ui_thread.start()
        logger.info("Web UI thread started")

        logger.info("All systems initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise

    yield

    # Cleanup with proper shutdown sequence
    logger.info("Shutting down LLM Proxy API")

    try:
        # Shutdown performance systems in reverse order
        if hasattr(app.state, 'memory_manager'):
            await shutdown_memory_manager()
            logger.info("Memory manager shutdown")

        if hasattr(app.state, 'response_cache'):
            await shutdown_caches()
            logger.info("Caches shutdown")

        logger.info("All performance systems shutdown successfully")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("LLM Proxy API shutdown complete")



# FastAPI app setup
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan
)

# Middleware setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(InvalidRequestError)
async def invalid_request_handler(request: Request, exc: InvalidRequestError):
    return JSONResponse(status_code=400, content=exc.to_dict())

@app.exception_handler(AuthenticationError)
async def authentication_handler(request: Request, exc: AuthenticationError):
    return JSONResponse(status_code=401, content=exc.to_dict())

@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    return JSONResponse(status_code=429, content=exc.to_dict())

@app.exception_handler(NotImplementedError)
async def not_implemented_handler(request: Request, exc: NotImplementedError):
    return JSONResponse(status_code=501, content=exc.to_dict())


@app.exception_handler(ServiceUnavailableError)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(status_code=503, content=exc.to_dict())

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    # Dynamically generate endpoints from app routes
    endpoints = {}
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/v1/'):
            endpoints[route.path.replace('/v1/', '')] = route.path
        elif route.path in ['/health', '/metrics', '/providers']:
            endpoints[route.path.lstrip('/')] = route.path
    
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "endpoints": endpoints
    }

@app.get("/health")
async def health_check(request: Request):
    """Comprehensive health check endpoint with performance metrics"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "uptime": time.time() - getattr(request.app.state, 'start_time', time.time()),
        "checks": {}
    }

    # Provider health
    try:
        enabled_providers = sum(1 for p in request.app.config.providers if p.enabled)
        health_status["checks"]["providers"] = {
            "status": "healthy" if enabled_providers > 0 else "unhealthy",
            "total": len(request.app.config.providers),
            "enabled": enabled_providers
        }
    except Exception as e:
        health_status["checks"]["providers"] = {"status": "error", "error": str(e)}

    # Memory health
    try:
        if hasattr(request.app.state, 'memory_manager'):
            memory_stats = request.app.state.memory_manager.get_memory_stats()
            memory_usage_percent = memory_stats.memory_percent

            health_status["checks"]["memory"] = {
                "status": "healthy" if memory_usage_percent < 90 else "warning" if memory_usage_percent < 95 else "critical",
                "usage_percent": memory_usage_percent,
                "used_mb": memory_stats.used_memory_mb,
                "available_mb": memory_stats.available_memory_mb
            }
        else:
            health_status["checks"]["memory"] = {"status": "not_initialized"}
    except Exception as e:
        health_status["checks"]["memory"] = {"status": "error", "error": str(e)}

    # Cache health
    try:
        if hasattr(request.app.state, 'response_cache'):
            cache_stats = request.app.state.response_cache.get_stats()
            health_status["checks"]["cache"] = {
                "status": "healthy",
                "entries": cache_stats['entries'],
                "hit_rate": cache_stats['hit_rate'],
                "memory_mb": cache_stats['memory_usage_mb']
            }
        else:
            health_status["checks"]["cache"] = {"status": "not_initialized"}
    except Exception as e:
        health_status["checks"]["cache"] = {"status": "error", "error": str(e)}

    # HTTP client health
    try:
        if hasattr(request.app.state, 'http_client'):
            client_metrics = request.app.state.http_client.get_metrics()
            health_status["checks"]["http_client"] = {
                "status": "healthy",
                "requests_total": client_metrics['requests_total'],
                "error_rate": client_metrics['error_rate'],
                "avg_response_time_ms": client_metrics['avg_response_time_ms']
            }
        else:
            health_status["checks"]["http_client"] = {"status": "not_initialized"}
    except Exception as e:
        health_status["checks"]["http_client"] = {"status": "error", "error": str(e)}

    # Circuit breaker health
    try:
        from src.core.circuit_breaker import get_circuit_breaker_metrics
        cb_metrics = get_circuit_breaker_metrics()
        open_breakers = sum(1 for m in cb_metrics.values() if m['state'] == 'open')

        health_status["checks"]["circuit_breakers"] = {
            "status": "healthy" if open_breakers == 0 else "warning",
            "total": len(cb_metrics),
            "open": open_breakers,
            "closed": len(cb_metrics) - open_breakers
        }
    except Exception as e:
        health_status["checks"]["circuit_breakers"] = {"status": "error", "error": str(e)}

    # Overall status determination
    critical_checks = ['providers', 'memory']
    if any(health_status["checks"].get(check, {}).get("status") in ["unhealthy", "critical", "error"]
           for check in critical_checks):
        health_status["status"] = "unhealthy"
    elif any(health_status["checks"].get(check, {}).get("status") == "warning"
             for check in health_status["checks"]):
        health_status["status"] = "warning"

    return health_status

@app.get("/metrics")
async def get_metrics(request: Request):
    """Comprehensive metrics endpoint with performance data"""
    base_metrics = metrics_collector.get_all_stats()

    # Add performance system metrics
    performance_metrics = {
        "performance": {},
        "system": {},
        "caches": {},
        "circuit_breakers": {}
    }

    # Memory metrics
    try:
        if hasattr(request.app.state, 'memory_manager'):
            memory_stats = request.app.state.memory_manager.get_memory_stats()
            performance_metrics["performance"]["memory"] = {
                "used_mb": memory_stats.process_memory_mb,
                "system_used_percent": memory_stats.memory_percent,
                "gc_collections": memory_stats.gc_collections
            }
    except Exception as e:
        performance_metrics["performance"]["memory"] = {"error": str(e)}

    # Cache metrics
    try:
        if hasattr(request.app.state, 'response_cache'):
            cache_stats = request.app.state.response_cache.get_stats()
            performance_metrics["caches"]["response_cache"] = cache_stats

        if hasattr(request.app.state, 'summary_cache_obj'):
            summary_stats = request.app.state.summary_cache_obj.get_stats()
            performance_metrics["caches"]["summary_cache"] = summary_stats
    except Exception as e:
        performance_metrics["caches"]["error"] = str(e)

    # HTTP client metrics
    try:
        if hasattr(request.app.state, 'http_client'):
            http_metrics = request.app.state.http_client.get_metrics()
            performance_metrics["performance"]["http_client"] = http_metrics
    except Exception as e:
        performance_metrics["performance"]["http_client"] = {"error": str(e)}

    # Circuit breaker metrics
    try:
        from src.core.circuit_breaker import get_circuit_breaker_metrics
        cb_metrics = get_circuit_breaker_metrics()
        performance_metrics["circuit_breakers"] = cb_metrics
    except Exception as e:
        performance_metrics["circuit_breakers"]["error"] = str(e)

    # System metrics
    try:
        import psutil
        performance_metrics["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
        }
    except Exception as e:
        performance_metrics["system"]["error"] = str(e)

    # Combine all metrics
    return {
        **base_metrics,
        **performance_metrics,
        "timestamp": time.time(),
        "version": settings.app_version
    }

@app.get("/providers")
async def list_providers():
    """List all providers and their capabilities"""
    return [
        {
            "name": provider.name,
            "type": provider.type,
            "models": provider.models,
            "enabled": provider.enabled,
            "priority": provider.priority
        }
        for provider in app.config.providers
    ]


@app.post("/v1/chat/completions", response_model=None)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def chat_completions(
    request: Request,
    background_tasks: BackgroundTasks,
    completion_request: ChatCompletionRequest,
    _: bool = Depends(verify_api_key)
) -> Union[Dict[str, Any], StreamingResponse]:
    """
    OpenAI-compatible chat completions endpoint with intelligent routing.

    Features:
    - Automatic provider failover
    - Context condensation for long conversations
    - Circuit breaker protection
    - Streaming support
    """
    model = completion_request.model
    if not model:
        raise InvalidRequestError("Model is required", param="model", code="missing_model")

    req = completion_request.dict(exclude_unset=True)

    # Handle context condensation
    condensation_response = await handle_context_condensation(
        request, background_tasks, req, "chat_completion"
    )
    if condensation_response:
        return condensation_response

    # Get providers and process request
    providers = get_providers_for_model(request, model)
    if not providers:
        raise InvalidRequestError(
            f"Model '{model}' is not supported by any provider",
            param="model",
            code="model_not_found"
        )

    return await process_request_with_fallback(
        request, req, providers, "chat_completion", background_tasks
    )

@app.post("/v1/completions", response_model=None)
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def completions(
    request: Request,
    background_tasks: BackgroundTasks,
    completion_request: TextCompletionRequest,
    _: bool = Depends(verify_api_key)
) -> Union[Dict[str, Any], StreamingResponse]:
    """
    OpenAI-compatible text completions endpoint with intelligent routing.

    Features:
    - Automatic provider failover
    - Context condensation for long prompts
    - Circuit breaker protection
    - Streaming support
    """
    model = completion_request.model
    if not model:
        raise InvalidRequestError("Model is required", param="model", code="missing_model")

    req = completion_request.dict(exclude_unset=True)

    # Handle context condensation for prompts
    config = request.app.state.condensation_config
    prompt = req.get("prompt", "")
    if isinstance(prompt, list):
        total_content = sum(len(p) for p in prompt)
    else:
        total_content = len(prompt)

    if total_content > config.truncation_threshold:
        request_id = str(uuid.uuid4())
        full_chunks = prompt if isinstance(prompt, list) else [prompt]
        background_tasks.add_task(background_condense, request_id, request, full_chunks)

        if not req.get("stream", False):
            return {
                "status": "processing",
                "request_id": request_id,
                "message": "Long prompt detected; summarization in progress. Poll /summary/{request_id} for result.",
                "estimated_time": "5-10 seconds"
            }

        # For streaming, truncate and proceed
        truncate_len = config.truncation_threshold // 2
        if isinstance(prompt, list):
            num_items_to_keep = max(1, len(prompt) * truncate_len // total_content)
            req["prompt"] = prompt[-num_items_to_keep:]
        else:
            req["prompt"] = prompt[-truncate_len:]
        logger.info(f"Proactive truncation for long prompt ({total_content} chars), background task added: {request_id}")

    # Get providers and process request
    providers = get_providers_for_model(request, model)
    if not providers:
        raise InvalidRequestError(
            f"Model '{model}' is not supported by any provider",
            param="model",
            code="model_not_found"
        )

    return await process_request_with_fallback(
        request, req, providers, "text_completion", background_tasks
    )

@app.post("/v1/embeddings")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def embeddings(
    request: Request,
    embedding_request: EmbeddingRequest,
    _: bool = Depends(verify_api_key)
) -> Dict[str, Any]:
    """
    OpenAI-compatible embeddings endpoint with intelligent routing.

    Features:
    - Automatic provider failover
    - Circuit breaker protection
    - Optimized for embedding workloads
    """
    model = embedding_request.model
    if not model:
        raise InvalidRequestError("Model is required", param="model", code="missing_model")

    req = embedding_request.dict(exclude_unset=True)

    # Get providers and process request
    providers = get_providers_for_model(request, model)
    if not providers:
        raise InvalidRequestError(
            f"Model '{model}' is not supported by any provider",
            param="model",
            code="model_not_found"
        )

    return await process_request_with_fallback(
        request, req, providers, "embeddings", BackgroundTasks()
    )

async def background_condense(request_id: str, request: Request, chunks: List[str]):
    """Background task to compute full context summary and store in smart cache"""
    try:
        start_time = time.time()
        summary = await condense_context(request, chunks)
        latency = time.time() - start_time

        # Store in smart cache with TTL
        cache_data = {
            "summary": summary,
            "timestamp": time.time(),
            "latency": latency,
            "chunks_count": len(chunks),
            "total_chars": sum(len(chunk) for chunk in chunks)
        }

        # Use smart cache for better performance
        if hasattr(request.app.state, 'summary_cache_obj'):
            await request.app.state.summary_cache_obj.set(
                f"summary_{request_id}",
                cache_data,
                ttl=3600  # 1 hour TTL for summaries
            )
        else:
            # Fallback to legacy cache
            request.app.state.summary_cache[request_id] = cache_data

        # Record metrics
        metrics_collector.record_summary(False, latency)

        logger.info(
            "Background summary stored",
            extra={
                'request_id': request_id,
                'latency': round(latency, 2),
                'chunks_count': len(chunks),
                'total_chars': sum(len(chunk) for chunk in chunks)
            }
        )

    except Exception as e:
        logger.error(
            "Background condensation failed",
            extra={'request_id': request_id, 'error': str(e)}
        )

        error_data = {"error": str(e), "timestamp": time.time()}

        # Store error in cache
        if hasattr(request.app.state, 'summary_cache_obj'):
            await request.app.state.summary_cache_obj.set(
                f"summary_{request_id}",
                error_data,
                ttl=300  # 5 minutes for errors
            )
        else:
            request.app.state.summary_cache[request_id] = error_data

@app.get("/summary/{request_id}")
async def get_summary_status(request_id: str, request: Request):
    """Poll for background summarization status with smart cache"""
    cache_key = f"summary_{request_id}"

    # Try smart cache first
    if hasattr(request.app.state, 'summary_cache_obj'):
        try:
            result = await request.app.state.summary_cache_obj.get(cache_key)
            if result is not None:
                if "error" in result:
                    return {
                        "status": "error",
                        "error": result["error"],
                        "timestamp": result["timestamp"]
                    }
                return {
                    "status": "completed",
                    "summary": result["summary"],
                    "timestamp": result["timestamp"],
                    "latency": result.get("latency", 0),
                    "cached": True
                }
        except Exception as e:
            logger.warning(f"Smart cache error for {request_id}: {e}")

    # Fallback to legacy cache
    legacy_cache = getattr(request.app.state, 'summary_cache', {})
    if request_id in legacy_cache:
        result = legacy_cache[request_id]
        if "error" in result:
            return {"status": "error", "error": result["error"], "timestamp": result["timestamp"]}
        return {
            "status": "completed",
            "summary": result["summary"],
            "timestamp": result["timestamp"],
            "latency": result.get("latency", 0),
            "cached": False
        }

    return {
        "status": "not_found",
        "message": "Request ID not found or processing not started",
        "request_id": request_id
    }

@app.get("/v1/models")
async def list_models(request: Request) -> Dict[str, Any]:
    """
    OpenAI-compatible models endpoint with comprehensive model information.

    Returns all available models across all enabled providers with metadata.
    """
    models = []
    for provider in request.app.config.providers:
        if provider.enabled:
            for model in provider.models:
                models.append({
                    "id": model,
                    "object": "model",
                    "created": int(datetime.now(timezone.utc).timestamp()),
                    "owned_by": provider.name,
                    "permission": [],  # OpenAI compatibility
                    "root": model,
                    "parent": None
                })

    return {
        "object": "list",
        "data": models
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", path=request.url.path)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "internal_error",
            "detail": "An unexpected error occurred"
        }
    )
            
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
