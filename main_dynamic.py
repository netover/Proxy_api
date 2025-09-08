import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict, Any, List
import time

from src.core.config import settings
from src.core.logging import setup_logging, ContextualLogger
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, check_rate_limit
from src.services.provider_loader import instantiate_providers


# Setup logging
setup_logging(
    log_level="DEBUG" if settings.debug else "INFO",
    log_file=settings.log_file
)
logger = ContextualLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("🚀 Starting LLM Proxy API")
    
    # Initialize providers dynamically
    try:
        app.state.providers = instantiate_providers()
        logger.info(f"Loaded {len(app.state.providers)} providers dynamically")
    except Exception as e:
        logger.error(f"Failed to load providers: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down LLM Proxy API")


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Helper function to find providers that support a model
def find_providers_for_model(providers, model: str):
    return [provider for provider in providers if model in provider.models]

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
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

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": len(app.state.providers) if hasattr(app.state, 'providers') else 0
    }

@app.get("/metrics")
async def get_metrics():
    """Provider metrics endpoint"""
    return metrics_collector.get_all_stats()

@app.get("/providers")
async def list_providers():
    """List all providers and their capabilities"""
    if not hasattr(app.state, 'providers'):
        return []
    
    return [
        {
            "name": provider.name,
            "models": provider.models,
            "priority": provider.priority
        }
        for provider in app.state.providers
    ]

@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def chat_completions(
    request: Request,
    completion_request: Dict[str, Any],
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible chat completions endpoint with intelligent routing"""

    if not hasattr(app.state, 'providers'):
        raise HTTPException(status_code=500, detail="Providers not loaded")

    model = completion_request.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    # Find providers that support this model
    providers = find_providers_for_model(app.state.providers, model)

    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Sort providers by priority (lower number = higher priority)
    providers.sort(key=lambda p: p.priority)

    # Try providers in order
    last_exception = None

    for provider in providers:
        try:
            logger.info(f"Attempting request with provider: {provider.name}")

            # Make the request
            response = await provider.create_completion(completion_request)

            logger.info("Request completed successfully",
                       provider=provider.name)

            return response

        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed", error=str(last_exception))
    raise HTTPException(
        status_code=503,
        detail="All providers are currently unavailable"
    )

@app.post("/v1/completions")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def completions(
    request: Request,
    completion_request: Dict[str, Any],
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible completions endpoint with intelligent routing"""

    if not hasattr(app.state, 'providers'):
        raise HTTPException(status_code=500, detail="Providers not loaded")

    model = completion_request.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    # Find providers that support this model
    providers = find_providers_for_model(app.state.providers, model)

    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Sort providers by priority (lower number = higher priority)
    providers.sort(key=lambda p: p.priority)

    # Try providers in order
    last_exception = None

    for provider in providers:
        try:
            logger.info(f"Attempting completions request with provider: {provider.name}")

            # Make the request
            response = await provider.create_text_completion(completion_request)

            logger.info("Completions request completed successfully",
                       provider=provider.name)

            return response

        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed for completions", error=str(last_exception))
    raise HTTPException(
        status_code=503,
        detail="All providers are currently unavailable"
    )

@app.post("/v1/embeddings")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def embeddings(
    request: Request,
    embedding_request: Dict[str, Any],
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible embeddings endpoint with intelligent routing"""

    if not hasattr(app.state, 'providers'):
        raise HTTPException(status_code=500, detail="Providers not loaded")

    model = embedding_request.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    # Find providers that support this model
    providers = find_providers_for_model(app.state.providers, model)

    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Sort providers by priority (lower number = higher priority)
    providers.sort(key=lambda p: p.priority)

    # Try providers in order
    last_exception = None

    for provider in providers:
        try:
            logger.info(f"Attempting embeddings request with provider: {provider.name}")

            # Make the request
            response = await provider.create_embeddings(embedding_request)

            logger.info("Embeddings request completed successfully",
                       provider=provider.name)

            return response

        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed for embeddings", error=str(last_exception))
    raise HTTPException(
        status_code=503,
        detail="All providers are currently unavailable"
    )

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    if not hasattr(app.state, 'providers'):
        return {"object": "list", "data": []}

    models = []
    for provider in app.state.providers:
        for model in provider.models:
            models.append({
                "id": model,
                "object": "model",
                "created": 1677610602,  # Default timestamp
                "owned_by": provider.name
            })
            
    return {
        "object": "list",
        "data": models
    }

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", path=request.url.path)
    
    return {
        "error": "Internal server error",
        "detail": "An unexpected error occurred"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
