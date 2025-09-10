import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from typing import Dict, Any, List
import time
from http import HTTPStatus
import httpx

from src.core.config import settings
from src.core.logging import setup_logging, ContextualLogger
from src.core.app_config import init_config
from src.core.metrics import metrics_collector
from src.core.auth import verify_api_key, check_rate_limit, APIKeyAuth
from src.providers.base import ProviderConfig, ProviderError, InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError, ServiceUnavailableError
from src.core.app_config import ChatCompletionRequest, CompletionRequest, EmbeddingRequest
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting LLM Proxy API")
    
    # Initialize configuration
    try:
        config = init_config()
        app.state.config = config
        app.config = config
        api_key_auth = APIKeyAuth(settings.proxy_api_keys)
        app.state.api_key_auth = api_key_auth
        app.state.provider_factories = get_provider_factories(config.providers)
        logger.info(f"Loaded {len(app.state.config.providers)} providers")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down LLM Proxy API")



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

@app.exception_handler(APIConnectionError)
async def api_connection_handler(request: Request, exc: APIConnectionError):
    return JSONResponse(status_code=500, content=exc.to_dict())

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
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "providers": len(app.config.providers)
    }

@app.get("/metrics")
async def get_metrics():
    """Provider metrics endpoint"""
    return metrics_collector.get_all_stats()

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

def get_providers_for_model(request: Request, model: str) -> List[ProviderConfig]:
    """Get sorted list of enabled providers that support the given model"""
    providers = [
        provider for provider in request.app.config.providers
        if provider.enabled and model in provider.models
    ]
    providers.sort(key=lambda p: p.priority)
    return providers

@app.post("/v1/chat/completions")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def chat_completions(
    request: Request,
    completion_request: ChatCompletionRequest,
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible chat completions endpoint with intelligent routing"""

    model = completion_request.model
    if not model:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Model is required")

    # Serialize to dict for consistency
    req = completion_request.dict(exclude_unset=True)

    # Find providers that support this model
    providers = get_providers_for_model(request, model)
        
    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Try providers in order
    last_exception = None

    for provider_config in providers:
        try:
            logger.info(f"Attempting request with provider: {provider_config.name}")

            # Get provider instance
            provider = get_provider(provider_config)
        
            # Wrap with circuit breaker
            circuit_breaker = get_circuit_breaker(f"provider_{provider_config.name}")

            async def try_completion(req):
                async def make_completion():
                    return await provider.create_completion(req)
                
                try:
                    # Make the request
                    response = await circuit_breaker.execute(make_completion)
                    return response
                except Exception as e:
                    msg = str(e).lower()
                    # Detecta erro de contexto longo
                    if ("context_length_exceeded" in msg or "maximum context length" in msg) and not req.get("stream", False):
                        # Condensa e reenvia
                        chunks = [m["content"] for m in req["messages"]]
                        summary = await condense_context(request, chunks, max_tokens=512)
                        req["messages"] = [
                            {"role": "system", "content": f"Resumo: {summary}"},
                            req["messages"][-1]
                        ]
                        logger.info("Contexto resumido automaticamente após erro", error=str(e))
                        # Retry with condensed context (disable stream for retry)
                        req["stream"] = False
                        async def make_retry():
                            return await provider.create_completion(req)
                        return await circuit_breaker.execute(make_retry)
                    raise e

            response = await try_completion(req)

            logger.info("Request completed successfully",
                       provider=provider_config.name)

            if hasattr(response, '__aiter__'):
                return StreamingResponse(response, media_type="text/event-stream")
            else:
                return response

        except (httpx.RequestError, ValueError, NotImplementedError) as e:
            last_exception = e
            logger.error(f"Provider {provider_config.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed", error=str(last_exception))
    raise ServiceUnavailableError("All providers are currently unavailable")

@app.post("/v1/completions")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def completions(
    request: Request,
    completion_request: CompletionRequest,
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible completions endpoint with intelligent routing"""

    model = completion_request.model
    if not model:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Model is required")

    # Find providers that support this model
    providers = get_providers_for_model(request, model)

    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Try providers in order
    last_exception = None

    for provider_config in providers:
        try:
            logger.info(f"Attempting completions request with provider: {provider_config.name}")

            # Get provider instance
            provider = get_provider(provider_config)
        
            # Wrap with circuit breaker
            circuit_breaker = get_circuit_breaker(f"provider_{provider_config.name}")
        
            async def make_text_completion():
                return await provider.create_text_completion(completion_request)
        
            # Make the request
            response = await circuit_breaker.execute(make_text_completion)

            logger.info("Completions request completed successfully",
                       provider=provider_config.name)

            if hasattr(response, '__aiter__'):
                return StreamingResponse(response, media_type="text/event-stream")
            else:
                return response

        except (httpx.RequestError, ValueError, NotImplementedError) as e:
            last_exception = e
            logger.error(f"Provider {provider_config.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed for completions", error=str(last_exception))
    raise ServiceUnavailableError("All providers are currently unavailable")

@app.post("/v1/embeddings")
@limiter.limit(f"{settings.rate_limit_requests}/{settings.rate_limit_window}second")
async def embeddings(
    request: Request,
    embedding_request: EmbeddingRequest,
    _: bool = Depends(verify_api_key)
):

    """OpenAI-compatible embeddings endpoint with intelligent routing"""

    model = embedding_request.model
    if not model:
        raise HTTPException(status_code=400, detail="Model is required")

    # Find providers that support this model
    providers = get_providers_for_model(request, model)
    
    if not providers:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{model}' is not supported by any provider"
        )

    # Try providers in order
    last_exception = None

    for provider_config in providers:
        try:
            logger.info(f"Attempting embeddings request with provider: {provider_config.name}")

            # Get provider instance
            provider = get_provider(provider_config)
        
            # Wrap with circuit breaker
            circuit_breaker = get_circuit_breaker(f"provider_{provider_config.name}")
        
            async def make_embeddings():
                return await provider.create_embeddings(embedding_request)
        
            # Make the request
            response = await circuit_breaker.execute(make_embeddings)

            logger.info("Embeddings request completed successfully",
                       provider=provider_config.name)

            return response

        except (httpx.RequestError, ValueError, NotImplementedError) as e:
            last_exception = e
            logger.error(f"Provider {provider_config.name} failed: {e}")
            continue

    # All providers failed
    logger.error("All providers failed for embeddings", error=str(last_exception))
    raise ServiceUnavailableError("All providers are currently unavailable")

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models endpoint"""
    models = []
    for provider in app.config.providers:
        if provider.enabled:
            for model in provider.models:
                models.append({
                    "id": model,
                    "object": "model",
                    "created": int(datetime.utcnow().timestamp()),  # Dynamic timestamp
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
