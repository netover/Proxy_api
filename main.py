"""
LLM Proxy API - Main Application Server
High-performance proxy with intelligent routing and fallback capabilities.
"""

import asyncio
import os
import threading
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Use orjson for faster JSON serialization if available
try:
    import orjson
except ImportError:
    orjson = None

# New API router imports
from src.api.router import (main_router, root_router, setup_exception_handlers,
                            setup_middleware)
from src.core.alerting import alert_manager
from src.core.app_state import app_state
from src.core.auth import APIKeyAuth
from src.core.chaos_engineering import chaos_monkey
# Core imports
from src.core.config import settings
# Performance optimization imports
from src.core.http_client_v2 import get_advanced_http_client
from src.core.logging import ContextualLogger, setup_logging
from src.core.memory_manager import get_memory_manager, shutdown_memory_manager
from src.core.provider_factory import provider_factory
from src.core.retry_strategies import RetryConfig
from src.core.smart_cache import (get_response_cache, get_summary_cache,
                                  shutdown_caches)
from src.core.cache_redis import RedisCacheAdapter
from src.core.telemetry import TracedSpan, telemetry

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
        config = app_state.config
        
        # Set config in app state for backward compatibility
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
            if hasattr(config.settings, "redis") and config.settings.redis.enabled:
                logger.info("Redis cache is enabled. Initializing RedisCacheAdapter.")
                redis_settings = config.settings.redis

                # Create a single Redis adapter and share it
                redis_adapter = RedisCacheAdapter(settings=redis_settings)
                await redis_adapter.start()

                # Assign the same adapter to all cache state variables
                app.state.response_cache = redis_adapter
                app.state.summary_cache_obj = redis_adapter
                app.state.lru_cache = redis_adapter

                span.set_attribute("cache.backend", "redis")
                logger.info("Redis cache adapter initialized and assigned.")

            else:
                logger.info("Redis cache is disabled. Falling back to in-memory caches.")
                app.state.response_cache = await get_response_cache()
                app.state.summary_cache_obj = await get_summary_cache()

                from src.utils.context_condenser import AsyncLRUCache
                persist_file = 'cache.json' if config.settings.condensation.cache_persist else None
                app.state.lru_cache = AsyncLRUCache(
                    maxsize=config.settings.condensation.cache_size,
                    persist_file=persist_file,
                    redis_url=None  # Ensure redis_url is not used
                )
                if persist_file:
                    await app.state.lru_cache.initialize()

                span.set_attribute("cache.backend", "in_memory")

            span.set_attribute("cache.initialized", True)
            logger.info("Caches initialized")

        # Initialize memory manager
        with TracedSpan("memory_manager.initialize") as span:
            app.state.memory_manager = await get_memory_manager()
            span.set_attribute("memory_manager.initialized", True)
            logger.info("Memory manager initialized")

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

        # The web UI is now started as a separate process.
        # See README.md for instructions.
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

        # Unified cache shutdown logic
        # The response_cache is the primary cache object to check
        if hasattr(app.state, 'response_cache'):
            # If it's a Redis adapter, it's the single instance for all caches
            if isinstance(app.state.response_cache, RedisCacheAdapter):
                shutdown_tasks.append(app.state.response_cache.stop())
                logger.info("Queued Redis cache shutdown.")
            else:
                # Otherwise, it's the in-memory caches
                shutdown_tasks.append(shutdown_caches())
                logger.info("Queued in-memory smart cache shutdown.")
                # Also shut down the separate in-memory LRU cache if it exists
                if hasattr(app.state, 'lru_cache') and hasattr(app.state.lru_cache, 'shutdown'):
                     shutdown_tasks.append(app.state.lru_cache.shutdown())
                     logger.info("Queued in-memory LRU cache shutdown.")

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
