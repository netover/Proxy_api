import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from typing import Dict, Any, List, Callable, Awaitable
import time

from src.core.logging import setup_logging, ContextualLogger
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, APIKeyAuth
from src.core.app_state import app_state


logger = ContextualLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting LLM Proxy API")
    app.state.start_time = int(time.time())

    try:
        # Initialize the application state, which handles all component setup
        await asyncio.wait_for(app_state.initialize(), timeout=60.0)
        app.state.app_state = app_state
        app.state.config = app_state.config
        logger.info("Application state initialized successfully.")

        # Setup logging based on the loaded configuration
        log_level = app.state.config.logging.get("level", "INFO").upper()
        log_file = app.state.config.logging.get("file")
        setup_logging(log_level=log_level, log_file=log_file)

        logger.info("LLM Proxy API started successfully.")

    except asyncio.TimeoutError:
        logger.error("Application initialization timed out.")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    # Cleanup
    logger.info("Shutting down LLM Proxy API...")
    await app_state.shutdown()
    logger.info("LLM Proxy API shutdown complete.")


from src.middleware.security_headers import SecurityHeadersMiddleware

# FastAPI app setup
app = FastAPI(
    title="LLM Proxy API",
    version="2.0.0",
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

from src.api.router import (
    main_router,
    root_router,
    setup_exception_handlers,
    setup_middleware,
)
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Include API routers
app.include_router(root_router)
app.include_router(main_router)

# Setup middleware and exception handlers from the new API structure
setup_middleware(app)
setup_exception_handlers(app)

# Add legacy exception handler for rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


if __name__ == "__main__":
    # Setup logging with default
    setup_logging(log_level="INFO")

    # Check if running as bundled executable
    import sys

    is_bundled = getattr(sys, "frozen", False)

    if is_bundled:
        # When bundled, use the app object directly
        uvicorn.run(
            app, host="127.0.0.1", port=8000, reload=False, log_level="info"
        )
    else:
        # When running from source, use string import
        uvicorn.run(
            "main_dynamic:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info",
        )
