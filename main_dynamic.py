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

    # Initialize app state first
    try:
        await asyncio.wait_for(app_state.initialize(), timeout=30.0)
        app.state.app_state = app_state
        logger.info("AppState initialized successfully")
    except ModuleNotFoundError as e:
        logger.error(f"A required dependency is missing: {e}. Please install it.")
        logger.error("The application cannot start without all configured dependencies.")
        raise
    except asyncio.TimeoutError:
        logger.error("AppState initialization timed out after 30 seconds")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize AppState: {e}")
        raise

    # Load config from app_state after initialization
    try:
        config = app_state.config_manager.load_config()
        app.state.config = config
        logger.info(f"Loaded {len(config.providers)} providers dynamically")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise

    # Setup logging after config load
    setup_logging(
        log_level="DEBUG" if config.settings.debug else "INFO",
        log_file=config.settings.log_file
    )

    # Initialize authentication
    if not config.settings.api_keys:
        logger.warning("No API keys configured. All authenticated requests will be rejected.")
    app.state.api_key_auth = APIKeyAuth(config.settings.api_keys)

    yield

    # Cleanup
    logger.info("Shutting down LLM Proxy API, closing provider clients...")
    await app_state.shutdown()



# FastAPI app setup
app = FastAPI(
    title="LLM Proxy API",
    version="2.0.0",
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

from src.api.endpoints import create_router
router = create_router()
app.include_router(router, prefix="/v1")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    config = app_state.config_manager.load_config()
    return {
        "name": config.settings.app_name,
        "version": config.settings.app_version,
        "status": "operational",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "completions": "/v1/completions",
            "embeddings": "/v1/embeddings",
            "models": "/v1/models",
            "health": "/health",
            "metrics": "/metrics",
            "providers": "/providers"
        }
    }

# Error handlers
from src.core.exceptions import ProviderError, InvalidRequestError, RateLimitError, AuthenticationError, ServiceUnavailableError, NotImplementedError

@app.exception_handler(ProviderError)
async def provider_exception_handler(request: Request, exc: ProviderError):
    logger.error(f"Provider error: {exc}", path=request.url.path, exc_info=True)
    
    status_code = 500
    if isinstance(exc, InvalidRequestError):
        status_code = 400
    elif isinstance(exc, AuthenticationError):
        status_code = 401
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, ServiceUnavailableError):
        status_code = 503
    elif isinstance(exc, NotImplementedError):
        status_code = 501
    
    error_dict = exc.to_dict()
    if isinstance(exc, InvalidRequestError):
        error_dict["param"] = exc.param
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_dict
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", path=request.url.path, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error",
                "code": "internal_error",
                "detail": "An unexpected error occurred. Please check the logs for more information."
            }
        },
    )

if __name__ == "__main__":
    # Setup logging with default
    setup_logging(log_level="INFO")

    # Check if running as bundled executable
    import sys
    is_bundled = getattr(sys, 'frozen', False)

    if is_bundled:
        # When bundled, use the app object directly
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    else:
        # When running from source, use string import
        uvicorn.run(
            "main_dynamic:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
