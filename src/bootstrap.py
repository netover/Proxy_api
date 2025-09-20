import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from src.core.app_state import app_state
from src.core.logging import setup_logging, ContextualLogger
from src.api.router import root_router, main_router
from src.core.config.manager import get_config
from src.middleware.security_headers import SecurityHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.api.errors.error_handlers import (
    global_exception_handler,
    validation_exception_handler,
    http_exception_handler,
)
from slowapi.util import get_remote_address

# Initial, basic logging setup before config is loaded
setup_logging(log_level="INFO")
logger = ContextualLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting LLM Proxy API")

    try:
        # Initialize the application state, which handles all component setup
        await asyncio.wait_for(app_state.initialize(), timeout=60.0)
        app.state.app_state = app_state
        app.state.config = app_state.config
        logger.info("Application state initialized successfully.")

        # Re-configure logging based on the loaded configuration
        log_level = app.state.config.logging.get("level", "INFO").upper()
        setup_logging(log_level=log_level)

        logger.info("LLM Proxy API started successfully.")

    except asyncio.TimeoutError:
        logger.error("Application initialization timed out.")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise

    yield

    logger.info("Shutting down LLM Proxy API...")
    await app_state.shutdown()
    logger.info("LLM Proxy API shutdown complete.")

# Load configuration to get the version for OpenAPI docs
config = get_config()
app_version = config.app.get("version", "2.0.0") # Default to 2.0.0 if not found

# FastAPI app setup
app = FastAPI(
    title="LLM Proxy API",
    version=app_version,
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routers
app.include_router(root_router)
app.include_router(main_router)

# Add rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add global exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
