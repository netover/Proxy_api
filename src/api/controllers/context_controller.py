import time
from typing import List

import httpx
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.core.exceptions import ServiceUnavailableError
from src.core.logging import ContextualLogger
from src.core.metrics.metrics import metrics_collector

logger = ContextualLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# This timeout should be consistent with the one in main.py
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=30.0)


async def condense_context_via_service(
    request: Request, chunks: List[str], max_tokens: int = 512
) -> str:
    """Call the context condensation service via HTTP"""
    config = request.app.state.config
    context_service_url = config.services.get(
        "context_service_url", "http://localhost:8001"
    )

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                f"{context_service_url}/condense",
                json={"chunks": chunks, "max_tokens": max_tokens},
            )
            response.raise_for_status()
            result = response.json()
            return result["summary"]
    except httpx.RequestError as e:
        logger.error(f"Failed to call context service: {e}")
        raise ServiceUnavailableError("Context condensation service is unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Context service error: {e.response.status_code} - {e.response.text}"
        )
        raise ServiceUnavailableError("Context condensation service returned an error")


async def background_condense(request_id: str, request: Request, chunks: List[str]):
    """Background task to compute full context summary and store in smart cache"""
    try:
        start_time = time.time()
        summary = await condense_context_via_service(request, chunks)
        latency = time.time() - start_time

        cache_data = {
            "summary": summary,
            "timestamp": time.time(),
            "latency": latency,
            "chunks_count": len(chunks),
            "total_chars": sum(len(chunk) for chunk in chunks),
        }

        if hasattr(request.app.state, "summary_cache_obj"):
            await request.app.state.summary_cache_obj.set(
                f"summary_{request_id}", cache_data, ttl=3600
            )
        else:
            request.app.state.summary_cache[request_id] = cache_data

        metrics_collector.record_summary(False, latency)
        logger.info("Background summary stored", extra={"request_id": request_id})

    except Exception as e:
        logger.error(
            "Background condensation failed",
            extra={"request_id": request_id, "error": str(e)},
        )
        error_data = {"error": str(e), "timestamp": time.time()}
        if hasattr(request.app.state, "summary_cache_obj"):
            await request.app.state.summary_cache_obj.set(
                f"summary_{request_id}", error_data, ttl=300
            )
        else:
            request.app.state.summary_cache[request_id] = error_data


@router.get("/summary/{request_id}")
async def get_summary_status(request_id: str, request: Request):
    """Poll for background summarization status with smart cache"""
    # Rate limiting for this endpoint is now handled globally via config.yaml
    cache_key = f"summary_{request_id}"

    if hasattr(request.app.state, "summary_cache_obj"):
        try:
            result = await request.app.state.summary_cache_obj.get(cache_key)
            if result is not None:
                if "error" in result:
                    return {
                        "status": "error",
                        "error": result["error"],
                        "timestamp": result["timestamp"],
                    }
                return {
                    "status": "completed",
                    "summary": result["summary"],
                    "timestamp": result["timestamp"],
                    "latency": result.get("latency", 0),
                    "cached": True,
                }
        except Exception as e:
            logger.warning(f"Smart cache error for {request_id}: {e}")

    legacy_cache = getattr(request.app.state, "summary_cache", {})
    if request_id in legacy_cache:
        result = legacy_cache[request_id]
        if "error" in result:
            return {
                "status": "error",
                "error": result["error"],
                "timestamp": result["timestamp"],
            }
        return {
            "status": "completed",
            "summary": result["summary"],
            "timestamp": result["timestamp"],
            "latency": result.get("latency", 0),
            "cached": False,
        }

    return {
        "status": "not_found",
        "message": "Request ID not found or processing not started",
        "request_id": request_id,
    }
