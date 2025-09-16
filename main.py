"""
LLM Proxy API - Main Application Server
High-performance proxy with intelligent routing and fallback capabilities.
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# New API router imports
from src.api.router import (
    main_router,
    root_router,
    setup_exception_handlers,
    setup_middleware,
)
from src.core.alerting import alert_manager
from src.core.auth import APIKeyAuth
from src.core.chaos_engineering import chaos_monkey

# --- Core Unified Configuration ---
from src.core.unified_config import get_config, UnifiedConfig

# Initialize configuration early
config = get_config()

# --- Core Imports ---
from src.core.http_client_v2 import get_advanced_http_client
from src.core.logging import ContextualLogger, setup_logging
from src.core.memory_manager import get_memory_manager, shutdown_memory_manager
from src.core.retry_strategies import RetryConfig
from src.core.smart_cache import (
    get_response_cache,
    get_summary_cache,
    shutdown_caches,
)
from src.core.telemetry import TracedSpan, telemetry
from src.utils.context_condenser import AsyncLRUCache

# Setup logging with the unified configuration
log_level = os.getenv("LOG_LEVEL", config.logging.get("level", "INFO")).upper()
setup_logging(log_level=log_level)
logger = ContextualLogger(__name__)


# Rate limiting (to be configured in lifespan)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management with the new unified config."""
    logger.info("Starting LLM Proxy API...")

    # Set start time for uptime tracking
    app.state.start_time = time.time()
    app.state.config = config

    try:
        # --- Initialize Systems from Unified Config ---
        logger.info("Initializing systems with unified configuration...")

        # Configure OpenTelemetry
        telemetry.configure(config.telemetry)
        telemetry.instrument_fastapi(app)
        telemetry.instrument_httpx()
        logger.info("OpenTelemetry configured successfully")

        # Initialize HTTP client
        with TracedSpan("http_client.initialize"):
            http_client = get_advanced_http_client(config=config.http_client)
            await http_client.initialize()
            app.state.http_client = http_client
            logger.info("HTTP client initialized")

        # Initialize caches
        with TracedSpan("cache.initialize"):
            app.state.response_cache = await get_response_cache(config.caching)
            app.state.summary_cache_obj = await get_summary_cache(config.caching)
            logger.info("Smart caches initialized")

        # Initialize memory manager
        with TracedSpan("memory_manager.initialize"):
            app.state.memory_manager = await get_memory_manager(config.memory)
            logger.info("Memory manager initialized")

        # Initialize context condensation cache
        persist_file = "cache.json" if config.condensation.cache_persist else None
        app.state.lru_cache = AsyncLRUCache(
            maxsize=config.condensation.cache_size,
            persist_file=persist_file,
            redis_url=config.condensation.cache_redis_url,
        )
        if persist_file or config.condensation.cache_redis_url:
            await app.state.lru_cache.initialize()
        logger.info("Context condensation cache initialized")

        # Initialize authentication
        api_key_auth = APIKeyAuth(config.proxy_api_keys)
        app.state.api_key_auth = api_key_auth
        logger.info(f"Authentication initialized with {len(config.proxy_api_keys)} API key(s).")

        # Configure rate limiter
        from src.core.rate_limiter import rate_limiter
        # Configure rate limiter with the specific rate_limit settings
        rate_limiter.configure_from_settings(config.rate_limit)
        app.state.rate_limiter = rate_limiter
        logger.info("Per-route rate limiting configured")

        # Configure chaos engineering
        chaos_monkey.configure(config.chaos_engineering)
        logger.info("Chaos engineering configured")

        # Start alerting system
        with TracedSpan("alerting.initialize"):
            await alert_manager.start_monitoring()
            logger.info("Alerting system initialized and monitoring started")

        logger.warning("The integrated web UI has been disabled by default for stability. "
                       "Please run 'python web_ui.py' as a separate process.")

        logger.info("All systems initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    # --- Shutdown Sequence ---
    logger.info("Shutting down LLM Proxy API")
    try:
        shutdown_tasks = [
            shutdown_memory_manager(),
            shutdown_caches(),
            alert_manager.stop_monitoring(),
        ]
        if hasattr(app.state, "lru_cache") and app.state.lru_cache:
            shutdown_tasks.append(app.state.lru_cache.shutdown())

        await asyncio.gather(*shutdown_tasks, return_exceptions=True)
        logger.info("All primary systems shutdown successfully")

        # Cancel any remaining background tasks
        tasks = [t for t in asyncio.all_tasks() if t != asyncio.current_task()]
        if tasks:
            logger.info(f"Cancelling {len(tasks)} remaining background tasks")
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All background tasks cancelled")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)

    logger.info("LLM Proxy API shutdown complete")


# --- FastAPI App Setup ---
app = FastAPI(
    title=config.app.name,
    version=config.app.version,
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan,
)

# Include API routers
app.include_router(root_router)
app.include_router(main_router)

# Setup middleware and exception handlers from the new API structure
setup_middleware(app)
setup_exception_handlers(app)

# Add legacy exception handler for rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add core middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.app.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


if __name__ == "__main__":
    server_config = config.server
    uvicorn.run(
        "main:app",
        host=server_config.host,
        port=server_config.port,
        reload=server_config.reload,
        log_level=log_level.lower(),
    )
