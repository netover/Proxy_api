import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import Dict, Any, List, Callable, Awaitable
import time

from src.core.config import settings, load_providers_cfg
from src.core.logging import setup_logging, ContextualLogger
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, APIKeyAuth
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
    logger.info("Starting LLM Proxy API")
    app.state.start_time = int(time.time())
    
    # Initialize authentication
    if not settings.proxy_api_keys:
        logger.warning("No API keys configured. All authenticated requests will be rejected.")
    app.state.api_key_auth = APIKeyAuth(settings.proxy_api_keys)

    # Initialize providers dynamically
    try:
        provider_cfgs = load_providers_cfg(settings.config_file)
        app.state.providers = instantiate_providers(provider_cfgs)
        logger.info(f"Loaded {len(app.state.providers)} providers dynamically")
    except Exception as e:
        logger.error(f"Failed to load providers: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down LLM Proxy API, closing provider clients...")
    if hasattr(app.state, "providers"):
        for provider in app.state.providers:
            try:
                await provider.client.aclose()
                logger.info(f"Closed client for provider: {provider.name}")
            except Exception as e:
                logger.error(f"Error closing client for provider {provider.name}: {e}")



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

async def _route_request(
    request_data: Dict[str, Any],
    providers: List[Any],
    provider_method_name: str,
    request_type: str
):
    """
    Generic request router for different completion types.
    """
    if not providers:
        raise HTTPException(status_code=500, detail="Providers not loaded")

    model = request_data.get("model")
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    # Find providers that support this model
    supported_providers = find_providers_for_model(providers, model)

    if not supported_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Sort providers by priority (lower number = higher priority)
    supported_providers.sort(key=lambda p: p.priority)

    # Try providers in order
    last_exception = None

    for provider in supported_providers:
        try:
            logger.info(f"Attempting {request_type} request with provider: {provider.name}")

            # Get the actual method from the provider instance
            provider_method: Callable[[Dict[str, Any]], Awaitable[Any]] = getattr(provider, provider_method_name)

            # Make the request
            response = await provider_method(request_data)

            logger.info(f"{request_type.capitalize()} request completed successfully",
                       provider=provider.name)

            return response

        except NotImplementedError:
            # This provider does not support the requested operation.
            # This is not a failure, so we log it as info and continue to the next provider.
            logger.info(f"Provider {provider.name} does not implement {provider_method_name}. Trying next provider.")
            last_exception = NotImplementedError(f"The {request_type} operation is not implemented by any of the attempted providers.")
            continue
        except Exception as e:
            last_exception = e
            logger.error(f"Provider {provider.name} failed for {request_type}: {e}")
            continue

    # All providers failed
    logger.error(f"All providers failed for {request_type}", error=str(last_exception))

    # If the last exception was because the method is not implemented, return 501
    if isinstance(last_exception, NotImplementedError):
        raise HTTPException(
            status_code=501,
            detail=f"The requested operation '{request_type}' is not supported by any provider for the model '{model}'."
        )

    raise HTTPException(
        status_code=503,
        detail="All providers are currently unavailable"
    )

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
    completion_request: Dict[str, Any],
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible chat completions endpoint with intelligent routing"""
    return await _route_request(
        request_data=completion_request,
        providers=request.app.state.providers,
        provider_method_name="create_completion",
        request_type="chat completions"
    )

@app.post("/v1/completions")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def completions(
    completion_request: Dict[str, Any],
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible completions endpoint with intelligent routing"""
    return await _route_request(
        request_data=completion_request,
        providers=request.app.state.providers,
        provider_method_name="create_text_completion",
        request_type="completions"
    )

@app.post("/v1/embeddings")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def embeddings(
    embedding_request: Dict[str, Any],
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible embeddings endpoint with intelligent routing"""
    return await _route_request(
        request_data=embedding_request,
        providers=request.app.state.providers,
        provider_method_name="create_embeddings",
        request_type="embeddings"
    )

@app.get("/v1/models")
async def list_models(request: Request):
    """OpenAI-compatible models endpoint"""
    if not hasattr(request.app.state, 'providers'):
        return {"object": "list", "data": []}

    models = []
    for provider in request.app.state.providers:
        for model in provider.models:
            models.append({
                "id": model,
                "object": "model",
                "created": request.app.state.start_time,
                "owned_by": provider.name
            })
            
    return {
        "object": "list",
        "data": models
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
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
