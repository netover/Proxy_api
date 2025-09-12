"""
LLM Proxy API - Main Application Server
High-performance proxy with intelligent routing and fallback capabilities.
"""

import asyncio
import re

import uvicorn

# Use orjson for faster JSON serialization if available, fallback to json
try:
    import orjson
    def json_dumps(obj):
        return orjson.dumps(obj).decode('utf-8')

    def json_loads(s):
        return orjson.loads(s)
except ImportError:
    import json
    json_dumps = json.dumps
    json_loads = json.loads
import os
import threading
import time
import uuid
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

# HTTP client
import httpx
# FastAPI imports
from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# HTTP Timeouts - Critical fix to prevent hanging requests
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=30.0)
HEALTH_CHECK_TIMEOUT = httpx.Timeout(5.0, connect=2.0)

# System monitoring
try:
    import psutil
except ImportError:
    psutil = None

# New API router imports
from src.api.router import (main_router, root_router, setup_exception_handlers,
                            setup_middleware)
from src.core.app_state import app_state
from src.core.auth import APIKeyAuth
from src.core.chaos_engineering import chaos_monkey
from src.core.circuit_breaker import get_circuit_breaker
# Core imports
from src.core.config import settings
from src.core.exceptions import ProviderError, ServiceUnavailableError
from src.core.provider_factory import ProviderStatus
# Performance optimization imports
from src.core.http_client_v2 import get_advanced_http_client
from src.core.retry_strategies import RetryConfig
from src.core.logging import ContextualLogger, setup_logging
from src.core.memory_manager import get_memory_manager, shutdown_memory_manager
from src.core.alerting import alert_manager
from src.core.metrics import metrics_collector
from src.core.provider_factory import provider_factory
from src.core.smart_cache import (get_response_cache, get_summary_cache,
                                  shutdown_caches)
from src.core.telemetry import TracedSpan, telemetry, traced
from src.core.unified_config import ProviderConfig, config_manager

# Setup logging with environment variable support
import os
log_level = os.getenv("LOG_LEVEL", "DEBUG" if settings.debug else "INFO").upper()
setup_logging(
    log_level=log_level,
    log_file=settings.log_file
)
logger = ContextualLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


# Background Task Exception Handling
def safe_background_task(func):
    """Wrapper for background tasks with proper exception handling"""
    async def wrapper(*args, **kwargs):
        try:
            await func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info(f"Background task {func.__name__} was cancelled")
        except Exception as e:
            logger.error(f"Background task {func.__name__} failed: {e}", exc_info=True)
    return wrapper

# Utility Functions
@traced("get_provider", attributes={"operation": "provider_initialization"})
async def get_provider(provider_config: ProviderConfig) -> Any:
    """Get or create provider instance with enhanced caching and validation"""
    provider_name = provider_config.name

    # First, try to get cached provider
    provider = await provider_factory.get_provider(provider_name)

    if provider is not None:
        # Validate cached provider health
        if provider.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]:
            logger.debug(f"Using cached healthy provider: {provider_name}")
            return provider
        else:
            logger.warning(f"Cached provider {provider_name} is unhealthy (status: {provider.status}), refreshing...")
            # Remove unhealthy provider from cache
            if provider_name in provider_factory._providers:
                del provider_factory._providers[provider_name]

    # Create new provider instance with retry logic
    max_retries = 2
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            provider = await provider_factory.create_provider(provider_config)
            logger.info(f"Successfully created provider: {provider_name} (attempt {attempt + 1})")
            return provider

        except ValueError as e:
            # Configuration errors (disabled provider, etc.) - don't retry
            logger.error(f"Configuration error for provider {provider_name}: {e}")
            raise ProviderError(f"Provider configuration error: {e}")

        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Failed to create provider {provider_name} (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Failed to create provider {provider_name} after {max_retries + 1} attempts: {e}")

    # All retries failed
    raise ProviderError(f"Failed to initialize provider {provider_name} after retries: {last_exception}")


def get_providers_for_model(request: Request, model: str) -> List[ProviderConfig]:
    """Get sorted list of enabled providers that support the given model"""
    providers = [
        provider for provider in request.app.state.config.providers
        if provider.enabled and model in provider.models
    ]
    providers.sort(key=lambda p: p.priority)
    return providers


@traced("handle_context_condensation", attributes={"operation": "context_condensation"})
async def handle_context_condensation(
    request: Request,
    background_tasks: BackgroundTasks,
    req: Dict[str, Any],
    operation: str
) -> Optional[Dict[str, Any]]:
    """Handle context condensation for long requests"""
    config = request.app.state.condensation_config
    total_content = sum(len(m["content"]) for m in req.get("messages", []))

    # Add span attributes
    from opentelemetry import trace
    current_span = trace.get_current_span()
    current_span.set_attribute("condensation.total_content", total_content)
    current_span.set_attribute("condensation.threshold", config.truncation_threshold)
    current_span.set_attribute("condensation.operation", operation)

    if total_content > config.truncation_threshold:
        request_id = str(uuid.uuid4())
        full_chunks = [m["content"] for m in req["messages"]]
        background_tasks.add_task(safe_background_task(background_condense), request_id, request, full_chunks)

        current_span.set_attribute("condensation.triggered", True)
        current_span.set_attribute("condensation.request_id", request_id)
        current_span.set_attribute("condensation.chunks_count", len(full_chunks))

        if not req.get("stream", False):
            return JSONResponse(
                status_code=HTTPStatus.ACCEPTED,
                content={
                    "status": "processing",
                    "request_id": request_id,
                    "message": "Long context detected; summarization in progress. Poll /summary/{request_id} for result.",
                    "estimated_time": "5-10 seconds"
                }
            )

        # For streaming, truncate and proceed
        truncate_len = config.truncation_threshold // 2
        num_messages_to_keep = max(1, len(req["messages"]) * truncate_len // total_content)
        truncated_messages = req["messages"][-num_messages_to_keep:]
        req["messages"] = truncated_messages
        current_span.set_attribute("condensation.truncated", True)
        current_span.set_attribute("condensation.messages_kept", len(truncated_messages))
        logger.info(f"Proactive truncation for long context ({total_content} chars), background task added: {request_id}")

    return None


async def background_condense(request_id: str, request: Request, chunks: List[str]):
    """Background task to compute full context summary and store in smart cache"""
    try:
        start_time = time.time()
        summary = await condense_context_via_service(chunks)
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


@traced("process_request_with_fallback", attributes={"operation": "request_processing"})
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

    # Add span attributes
    from opentelemetry import trace
    current_span = trace.get_current_span()
    current_span.set_attribute("operation.type", operation)
    current_span.set_attribute("providers.count", len(providers))
    current_span.set_attribute("request.streaming", bool(req.get("stream", False)))
    if "model" in req:
        current_span.set_attribute("request.model", req["model"])

    for idx, provider_config in enumerate(providers):
        try:
            with TracedSpan("provider.attempt", attributes={
                "provider.name": provider_config.name,
                "provider.priority": provider_config.priority,
                "attempt.number": idx + 1
            }) as provider_span:
                logger.info(f"Attempting {operation} with provider: {provider_config.name}")

                provider = await get_provider(provider_config)
                if not provider:
                    provider_span.set_attribute("provider.skipped", True)
                    continue

                circuit_breaker = get_circuit_breaker(f"provider_{provider_config.name}")
                provider_span.set_attribute("circuit_breaker.state", circuit_breaker.state)

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
                start_time = time.time()
                response = await circuit_breaker.execute(lambda: method(req))
                latency = time.time() - start_time

                provider_span.set_attribute("provider.success", True)
                provider_span.set_attribute("request.latency", latency)
                provider_span.set_attribute("response.streaming", hasattr(response, '__aiter__'))

                # Handle streaming responses
                if hasattr(response, '__aiter__'):
                    return StreamingResponse(response, media_type="text/event-stream")

                logger.info(f"{operation} successful", provider=provider_config.name)
                return response

        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider_config.name} failed: {e}")
            current_span.set_attribute(f"provider.{provider_config.name}.error", str(e))

            # Handle context length errors
            msg = str(e)
            if any(re.search(pattern, msg, re.IGNORECASE) for pattern in config.error_patterns):
                if not req.get("stream", False):
                    request_id = str(uuid.uuid4())
                    chunks = [m["content"] for m in req.get("messages", [])]
                    background_tasks.add_task(safe_background_task(background_condense), request_id, request, chunks)

                    return JSONResponse(
                        status_code=HTTPStatus.ACCEPTED,
                        content={
                            "status": "processing",
                            "request_id": request_id,
                            "message": f"Context error detected; summarization in progress. Poll /summary/{request_id} for result.",
                            "estimated_time": "5-10 seconds"
                        }
                    )

                # Truncate for streaming
                req["messages"] = req["messages"][-len(req["messages"])//2:]
                req["stream"] = False

            continue

    # All providers failed
    current_span.set_attribute("providers.failed", True)
    current_span.set_attribute("final_error", str(last_exception))
    logger.error(f"All providers failed for {operation}", error=str(last_exception))
    raise ServiceUnavailableError("All providers are currently unavailable")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with performance optimizations"""
    logger.info("Starting LLM Proxy API with performance optimizations")

    # Set start time for uptime tracking
    app.state.start_time = time.time()

    # Initialize configuration
    try:
        # Initialize app state with the new approach
        await app_state.initialize()
        
        # Set config in app state for backward compatibility
        config = app_state.config_manager.load_config()
        app.state.config = config
        app.state.condensation_config = config.settings.condensation

        # Initialize performance systems
        logger.info("Initializing performance optimization systems...")
    
        # Configure OpenTelemetry
        telemetry.configure(settings)
        telemetry.instrument_fastapi(app)
        telemetry.instrument_httpx()
        logger.info("OpenTelemetry configured successfully")
    
        # Initialize HTTP client
        with TracedSpan("http_client.initialize") as span:
            http_client = get_advanced_http_client(retry_config=RetryConfig())
            await http_client.initialize()
            app.state.http_client = http_client
            span.set_attribute("http.client.initialized", True)
            logger.info("HTTP client initialized")
    
        # Initialize caches
        with TracedSpan("cache.initialize") as span:
            app.state.response_cache = await get_response_cache()
            app.state.summary_cache_obj = await get_summary_cache()
            span.set_attribute("cache.response.initialized", True)
            span.set_attribute("cache.summary.initialized", True)
            logger.info("Smart caches initialized")
    
        # Initialize memory manager
        with TracedSpan("memory_manager.initialize") as span:
            app.state.memory_manager = await get_memory_manager()
            span.set_attribute("memory_manager.initialized", True)
            logger.info("Memory manager initialized")

        # Initialize context condensation cache with persistence
        from src.utils.context_condenser import AsyncLRUCache
        persist_file = 'cache.json' if config.settings.condensation.cache_persist else None
        redis_url = getattr(config.settings.condensation, 'cache_redis_url', None)
        app.state.lru_cache = AsyncLRUCache(
            maxsize=config.settings.condensation.cache_size,
            persist_file=persist_file,
            redis_url=redis_url
        )
        if persist_file:
            await app.state.lru_cache.initialize()
        logger.info("Context condensation cache initialized")

        # Legacy cache support (for backward compatibility)
        app.state.cache = {}
        app.state.summary_cache = {}

        # Initialize authentication
        api_key_auth = APIKeyAuth(settings.proxy_api_keys)
        app.state.api_key_auth = api_key_auth

        # Configure rate limiter
        from src.core.rate_limiter import rate_limiter
        rate_limiter.configure_from_config(config)
        app.state.rate_limiter = rate_limiter
        logger.info("Rate limiter configured and initialized")

        # Configure chaos engineering
        chaos_monkey.configure(config.settings.get('chaos_engineering', {}))
        logger.info("Chaos engineering configured")

        # Start alerting system
        with TracedSpan("alerting.initialize") as span:
            await alert_manager.start_monitoring()
            span.set_attribute("alerting.initialized", True)
            logger.info("Alerting system initialized and monitoring started")

        app.state.config_mtime = app_state.config_manager._last_modified

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

    # Cleanup with proper shutdown sequence - CRITICAL FIX FOR RACE CONDITIONS
    logger.info("Shutting down LLM Proxy API")

    try:
        # Shutdown app state first
        await app_state.shutdown()
        logger.info("App state shutdown complete")

        # Shutdown performance systems in reverse order with proper async handling
        shutdown_tasks = []

        if hasattr(app.state, 'memory_manager'):
            shutdown_tasks.append(shutdown_memory_manager())

        if hasattr(app.state, 'response_cache'):
            shutdown_tasks.append(shutdown_caches())

        # Shutdown context condensation cache
        if hasattr(app.state, 'lru_cache') and app.state.lru_cache:
            shutdown_tasks.append(app.state.lru_cache.shutdown())

        # Shutdown alerting system
        shutdown_tasks.append(alert_manager.stop_monitoring())

        # Wait for all shutdown tasks to complete
        if shutdown_tasks:
            await asyncio.gather(*shutdown_tasks, return_exceptions=True)
            logger.info("All performance systems shutdown successfully")

        # Cancel any remaining background tasks
        tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if tasks:
            logger.info(f"Cancelling {len(tasks)} remaining background tasks")
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Wait for cancelled tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All background tasks cancelled")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

    logger.info("LLM Proxy API shutdown complete")



# FastAPI app setup
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan
)

# Include new API routers
app.include_router(root_router)
app.include_router(main_router)

# Setup middleware and exception handlers from new API structure
setup_middleware(app)
setup_exception_handlers(app)

# Legacy middleware setup (keeping for compatibility)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers are now managed by the new error handling framework in src/api/errors/

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Root endpoint is now handled by root_router in src/api/router.py

# Health endpoint is now handled by health_controller in src/api/controllers/health_controller.py

# Metrics endpoint is now handled by analytics_controller in src/api/controllers/analytics_controller.py

# Providers endpoint is now handled by model_controller in src/api/controllers/model_controller.py


# API endpoints are now handled by the new thin controllers in src/api/controllers/

async def perform_parallel_health_checks() -> Dict[str, Any]:
    """Perform health checks in parallel for better performance - PERFORMANCE OPTIMIZATION"""
    logger.info("Starting parallel health checks")

    # Get all providers
    config = config_manager.load_config()
    providers = config.providers

    async def check_provider_health(provider: ProviderConfig) -> Dict[str, Any]:
        """Check individual provider health"""
        try:
            provider_instance = await get_provider(provider)
            if not provider_instance:
                return {
                    "name": provider.name,
                    "status": "error",
                    "error": "Failed to initialize provider"
                }

            # Quick health check
            start_time = time.time()
            result = await provider_instance.health_check()
            response_time = time.time() - start_time

            return {
                "name": provider.name,
                "status": "healthy" if result.get("healthy", False) else "unhealthy",
                "response_time": response_time,
                "details": result
            }
        except Exception as e:
            return {
                "name": provider.name,
                "status": "error",
                "error": str(e)
            }

    # Create tasks for parallel execution
    tasks = [check_provider_health(provider) for provider in providers]

    # Execute all health checks concurrently with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=30.0  # 30 second timeout for all checks
        )
    except asyncio.TimeoutError:
        logger.error("Parallel health checks timed out")
        results = [{"name": "timeout", "status": "error", "error": "Health check timeout"}]

    # Process results
    health_results = {}
    healthy_count = 0
    total_count = len(providers)

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Health check task failed: {result}")
            continue

        health_results[result["name"]] = result
        if result["status"] == "healthy":
            healthy_count += 1

    logger.info(f"Parallel health checks completed: {healthy_count}/{total_count} providers healthy")

    return {
        "timestamp": time.time(),
        "total_providers": total_count,
        "healthy_providers": healthy_count,
        "unhealthy_providers": total_count - healthy_count,
        "providers": health_results
    }

async def condense_context_via_service(chunks: List[str], max_tokens: int = 512) -> str:
    """Call the context condensation service via HTTP"""
    context_service_url = os.getenv("CONTEXT_SERVICE_URL", "http://localhost:8001")

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{context_service_url}/condense",
                json={"chunks": chunks, "max_tokens": max_tokens}
            )
            response.raise_for_status()
            result = response.json()
            return result["summary"]
    except httpx.RequestError as e:
        logger.error(f"Failed to call context service: {e}")
        raise ServiceUnavailableError("Context condensation service is unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"Context service error: {e.response.status_code} - {e.response.text}")
        raise ServiceUnavailableError("Context condensation service returned an error")

async def background_condense(request_id: str, request: Request, chunks: List[str]):
    """Background task to compute full context summary and store in smart cache"""
    try:
        start_time = time.time()
        summary = await condense_context_via_service(chunks)
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
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
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

# Additional models endpoint is now handled by the new model controller

# Global exception handler is now managed by the error handling framework in src/api/errors/
            
if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=log_level.lower()
    )
