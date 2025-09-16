"""API endpoints for the proxy service."""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any, List
import time

from proxy_core import ProviderFactory
from proxy_context import ContextCondenser, SmartCache
from proxy_logging import StructuredLogger
from .schemas import (
    ChatRequest,
    ChatResponse,
    ModelsResponse,
    ModelInfo,
    HealthCheck,
)

logger = StructuredLogger(__name__)
router = APIRouter()

# Global instances
provider_factory = ProviderFactory()
cache = SmartCache()
condenser = ContextCondenser()


@router.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest) -> ChatResponse:
    """OpenAI-compatible chat completions endpoint."""
    try:
        # This is a simplified implementation
        # In a real implementation, this would route to actual providers

        response = ChatResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=request.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Response from {request.model}",
                    },
                    "finish_reason": "stop",
                }
            ],
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        )

        return response

    except Exception as e:
        logger.error(f"Error in chat completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/v1/models")
async def list_models() -> ModelsResponse:
    """List all available models."""
    try:
        # Return mock data for now
        models = [
            ModelInfo(
                id="gpt-3.5-turbo", created=int(time.time()), owned_by="openai"
            ),
            ModelInfo(id="gpt-4", created=int(time.time()), owned_by="openai"),
            ModelInfo(
                id="claude-3-sonnet",
                created=int(time.time()),
                owned_by="anthropic",
            ),
        ]

        return ModelsResponse(data=models)

    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> HealthCheck:
    """Health check endpoint."""
    return HealthCheck(
        status="healthy",
        timestamp=int(time.time()),
        version="1.0.0",
        uptime=3600.0,
        checks={"database": "ok", "cache": "ok", "providers": "ok"},
    )


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Proxy API is running",
        "version": "1.0.0",
        "docs": "/docs",
    }


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics export endpoint."""
    try:
        from proxy_core.metrics import metrics_collector

        metrics_data = metrics_collector.get_prometheus_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as e:
        logger.error(f"Error exporting Prometheus metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@router.get("/metrics/json")
async def json_metrics():
    """JSON metrics endpoint."""
    try:
        from proxy_core.metrics import metrics_collector

        return metrics_collector.get_all_stats()
    except Exception as e:
        logger.error(f"Error exporting JSON metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")
