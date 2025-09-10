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

from src.core.unified_config import config_manager
from src.core.logging import setup_logging, ContextualLogger
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, APIKeyAuth
from src.core.provider_factory import provider_factory
from src.api.endpoints import router


# Setup logging
config = config_manager.load_config()
setup_logging(
    log_level="DEBUG" if config.settings.debug else "INFO",
    log_file=config.settings.log_file
)
logger = ContextualLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting LLM Proxy API")
    app.state.start_time = int(time.time())
    
    # Load config
    config = config_manager.load_config()
    app.state.config = config
    
    # Initialize authentication
    if not config.settings.api_keys:
        logger.warning("No API keys configured. All authenticated requests will be rejected.")
    app.state.api_key_auth = APIKeyAuth(config.settings.api_keys)

    # Initialize providers dynamically
    try:
        app.state.providers = await provider_factory.initialize_providers(config.providers)
        logger.info(f"Loaded {len(app.state.providers)} providers dynamically")
    except Exception as e:
        logger.error(f"Failed to load providers: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down LLM Proxy API, closing provider clients...")
    await provider_factory.shutdown()



# FastAPI app setup
app = FastAPI(
    title=config.settings.app_name,
    version=config.settings.app_version,
    description="High-performance LLM proxy with intelligent routing and fallback",
    lifespan=lifespan
)

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(router, prefix="/v1")

@app.get("/")
async def root():
    """Root endpoint with API information"""
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
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", path=request.url.path, exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "server_error",
                "detail": "An unexpected error occurred. Please check the logs for more information."
            }
        },
    )

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.settings.host,
        port=config.settings.port,
        reload=config.settings.debug,
        log_level="debug" if config.settings.debug else "info"
    )
