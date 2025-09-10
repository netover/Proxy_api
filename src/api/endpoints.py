from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import time
from contextlib import asynccontextmanager

from src.core.provider_factory import ProviderStatus
from src.core.auth import verify_api_key
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from src.core.rate_limiter import rate_limiter
from src.models.requests import (
    ChatCompletionRequest, 
    TextCompletionRequest, 
    EmbeddingRequest
)

logger = ContextualLogger(__name__)
router = APIRouter()

class RequestRouter:
    """Centralized request routing with intelligent fallback"""
    
    def __init__(self):
        self.circuit_breakers = {}
    
    async def route_request(self,
                          request: Request,
                          request_data: Union[ChatCompletionRequest, TextCompletionRequest, EmbeddingRequest],
                          operation: str,
                          background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """
        Generic request router with comprehensive error handling and fallback
        """
        app_state = request.app.state.app_state
        request_id = f"{operation}_{int(time.time() * 1000)}"
        logger.set_context(request_id=request_id, operation=operation, model=request_data.model)
        
        # Get providers for the model
        providers = await app_state.provider_factory.get_providers_for_model(request_data.model)
        
        if not providers:
            logger.error("No providers available for model", model=request_data.model)
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"Model '{request_data.model}' is not supported by any available provider",
                        "type": "invalid_request_error",
                        "param": "model",
                        "code": "model_not_found"
                    }
                }
            )
        
        # Track attempts for metrics
        attempt_info = []
        last_exception = None
        
        # Try providers in priority order
        for i, provider in enumerate(providers):
            attempt_start = time.time()
            
            try:
                logger.info(f"Attempting {operation} with provider {provider.name} (attempt {i+1}/{len(providers)})")
                
                # Choose the appropriate method based on operation
                if operation == "chat_completion":
                    result = await provider.create_completion(request_data.dict(exclude_unset=True))
                elif operation == "text_completion":
                    result = await provider.create_text_completion(request_data.dict(exclude_unset=True))
                elif operation == "embeddings":
                    result = await provider.create_embeddings(request_data.dict(exclude_unset=True))
                else:
                    raise ValueError(f"Unknown operation: {operation}")
                
                attempt_time = time.time() - attempt_start
                
                # Record successful attempt
                attempt_info.append({
                    "provider": provider.name,
                    "success": True,
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })
                
                # Log success and record metrics
                logger.info(f"{operation} successful",
                          provider=provider.name,
                          response_time=attempt_time,
                          total_attempts=i + 1)
                
                # Background task to record detailed metrics
                background_tasks.add_task(
                    self._record_success_metrics,
                    request_id, operation, provider.name, attempt_time, attempt_info
                )
                
                # Add provider info to response
                if isinstance(result, dict):
                    result.setdefault("_proxy_info", {}).update({
                        "provider": provider.name,
                        "attempt_number": i + 1,
                        "response_time": attempt_time,
                        "request_id": request_id
                    })
                
                return result
                
            except NotImplementedError:
                # Provider doesn't support this operation
                attempt_time = time.time() - attempt_start
                attempt_info.append({
                    "provider": provider.name,
                    "success": False,
                    "error": "operation_not_supported",
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })
                
                logger.info(f"Provider {provider.name} doesn't support {operation}, trying next")
                continue
                
            except Exception as e:
                attempt_time = time.time() - attempt_start
                last_exception = e
                
                # Record failed attempt
                attempt_info.append({
                    "provider": provider.name,
                    "success": False,
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })
                
                logger.error(f"Provider {provider.name} failed for {operation}",
                           error=str(e),
                           error_type=type(e).__name__,
                           response_time=attempt_time)
                
                # Continue to next provider
                continue
        
        # All providers failed
        logger.error(f"All providers failed for {operation}",
                    total_providers=len(providers),
                    attempts=len(attempt_info))
        
        # Background task to record failure metrics
        background_tasks.add_task(
            self._record_failure_metrics,
            request_id, operation, attempt_info
        )
        
        # Determine appropriate error response
        if all(attempt["error"] == "operation_not_supported" for attempt in attempt_info):
            raise HTTPException(
                status_code=501,
                detail={
                    "error": {
                        "message": f"The {operation} operation is not supported by any provider for model '{request_data.model}'",
                        "type": "not_implemented_error",
                        "code": "operation_not_supported"
                    }
                }
            )
        else:
            errors = [
                {
                    "provider": attempt["provider"],
                    "error_type": attempt["error"],
                    "error_message": attempt.get("error_message", "Unknown error")
                }
                for attempt in attempt_info if not attempt["success"]
            ]
            raise HTTPException(
                status_code=503,
                detail={
                    "error": {
                        "message": "All providers are currently unavailable",
                        "type": "service_unavailable_error",
                        "code": "providers_unavailable",
                        "details": {
                            "attempts": len(attempt_info),
                            "providers_tried": [a["provider"] for a in attempt_info],
                            "errors": errors,
                            "last_error": str(last_exception) if last_exception else None
                        }
                    }
                }
            )
    
    async def _record_success_metrics(self, request_id: str, operation: str, 
                                    provider_name: str, response_time: float,
                                    attempt_info: List[Dict]) -> None:
        """Background task to record detailed success metrics"""
        try:
            metrics_collector.record_request(
                provider_name,
                success=True,
                response_time=response_time,
                operation=operation,
                attempts=len(attempt_info)
            )
        except Exception as e:
            logger.error(f"Failed to record success metrics: {e}")
    
    async def _record_failure_metrics(self, request_id: str, operation: str,
                                    attempt_info: List[Dict]) -> None:
        """Background task to record detailed failure metrics"""
        try:
            for attempt in attempt_info:
                if not attempt["success"]:
                    metrics_collector.record_request(
                        attempt["provider"],
                        success=False,
                        response_time=attempt["response_time"],
                        error_type=attempt.get("error", "unknown"),
                        operation=operation
                    )
        except Exception as e:
            logger.error(f"Failed to record failure metrics: {e}")

# Global router instance
request_router = RequestRouter()

# Optimized endpoints with reduced duplication
@router.post("/v1/chat/completions")
@rate_limiter.limit("100/minute")
async def chat_completions(
    request: Request,
    completion_request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible chat completions endpoint"""
    result = await request_router.route_request(
        request,
        completion_request,
        "chat_completion",
        background_tasks
    )
    if completion_request.stream:
        return StreamingResponse(result, media_type="text/event-stream")
    return result

@router.post("/v1/completions")
@rate_limiter.limit("100/minute")
async def text_completions(
    request: Request,
    completion_request: TextCompletionRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible text completions endpoint"""
    result = await request_router.route_request(
        request,
        completion_request,
        "text_completion",
        background_tasks
    )
    if completion_request.stream:
        return StreamingResponse(result, media_type="text/event-stream")
    return result

@router.post("/v1/embeddings")
@rate_limiter.limit("200/minute")
async def embeddings(
    request: Request,
    embedding_request: EmbeddingRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible embeddings endpoint"""
    return await request_router.route_request(
        request,
        embedding_request,
        "embeddings",
        background_tasks
    )

# Enhanced utility endpoints
@router.get("/v1/models")
async def list_models(request: Request):
    """List all available models across providers"""
    app_state = request.app.state.app_state
    config = app_state.config_manager.load_config()
    provider_info = await app_state.provider_factory.get_all_provider_info()
    
    models = []
    for provider in provider_info:
        if provider.status in [ProviderStatus.HEALTHY, ProviderStatus.DEGRADED]:
            for model in provider.models:
                models.append({
                    "id": model,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": provider.name,
                    "provider_type": provider.type.value,
                    "status": provider.status.value
                })
    
    return {
        "object": "list",
        "data": models
    }

@router.get("/health")
async def health_check(request: Request):
    """Comprehensive health check"""
    app_state = request.app.state.app_state
    provider_info = await app_state.provider_factory.get_all_provider_info()
    
    healthy_count = sum(1 for p in provider_info
                       if p.status == ProviderStatus.HEALTHY)
    total_count = len(provider_info)
    
    overall_status = "healthy" if healthy_count > 0 else "unhealthy"
    
    return {
        "status": overall_status,
        "timestamp": time.time(),
        "providers": {
            "total": total_count,
            "healthy": healthy_count,
            "degraded": sum(1 for p in provider_info if p.status == ProviderStatus.DEGRADED),
            "unhealthy": sum(1 for p in provider_info if p.status == ProviderStatus.UNHEALTHY),
            "disabled": sum(1 for p in provider_info if p.status == ProviderStatus.DISABLED)
        },
        "details": [
            {
                "name": p.name,
                "type": p.type.value,
                "status": p.status.value,
                "models": len(p.models),
                "last_check": p.last_health_check,
                "error_count": p.error_count
            }
            for p in provider_info
        ]
    }

@router.get("/metrics")
async def get_metrics(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """Comprehensive metrics endpoint"""
    app_state = request.app.state.app_state
    metrics = metrics_collector.get_all_stats()
    provider_info = await app_state.provider_factory.get_all_provider_info()
    
    # Add provider status to metrics
    for provider_name, provider_metrics in metrics.items():
        provider = next((p for p in provider_info if p.name == provider_name), None)
        if provider:
            provider_metrics.update({
                "status": provider.status.value,
                "models": provider.models,
                "priority": provider.priority,
                "last_health_check": provider.last_health_check,
                "error_count": provider.error_count
            })
    
    return {
        "timestamp": time.time(),
        "providers": metrics,
        "summary": {
            "total_providers": len(provider_info),
            "total_requests": sum(m.get("total_requests", 0) for m in metrics.values()),
            "average_success_rate": sum(m.get("success_rate", 0) for m in metrics.values()) / max(len(metrics), 1)
        }
    }

@router.get("/providers")
async def list_providers(
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """List all configured providers with detailed information"""
    app_state = request.app.state.app_state
    provider_info = await app_state.provider_factory.get_all_provider_info()
    
    return {
        "providers": [
            {
                "name": p.name,
                "type": p.type.value,
                "status": p.status.value,
                "models": p.models,
                "priority": p.priority,
                "last_health_check": p.last_health_check,
                "error_count": p.error_count,
                "last_error": p.last_error
            }
            for p in provider_info
        ]
    }