import time

from fastapi import APIRouter, Depends, Request, Response

from src.core.auth import verify_api_key
from src.core.logging import ContextualLogger
from src.core.metrics.metrics import metrics_collector

logger = ContextualLogger(__name__)

router = APIRouter()


@router.get("/metrics")
async def get_metrics(request: Request, _: bool = Depends(verify_api_key)):
    """Comprehensive metrics endpoint"""
    start_time = time.time()
    logger.info("Metrics request started")

    app_state = request.app.state.app_state
    metrics = app_state.metrics_collector.get_metrics()
    provider_info = await app_state.provider_factory.get_all_provider_info()

    # Add provider status to metrics
    for provider_name, provider_metrics in metrics.items():
        provider = next((p for p in provider_info if p.name == provider_name), None)
        if provider:
            provider_metrics.update(
                {
                    "status": provider.status.value,
                    "models": provider.models,
                    "priority": provider.priority,
                    "enabled": provider.enabled,
                    "forced": provider.forced,
                    "last_health_check": provider.last_health_check,
                    "error_count": provider.error_count,
                }
            )

    response_time = time.time() - start_time
    total_requests = sum(m.get("total_requests", 0) for m in metrics.values())
    avg_success_rate = sum(m.get("success_rate", 0) for m in metrics.values()) / max(
        len(metrics), 1
    )

    logger.info(
        "Metrics retrieved",
        response_time=response_time,
        provider_count=len(provider_info),
        total_requests=total_requests,
        average_success_rate=round(avg_success_rate, 3),
    )

    return {
        "timestamp": time.time(),
        "providers": metrics,
        "summary": {
            "total_providers": len(provider_info),
            "total_requests": total_requests,
            "average_success_rate": avg_success_rate,
        },
    }


@router.get("/metrics/prometheus")
async def get_prometheus_metrics(request: Request, _: bool = Depends(verify_api_key)):
    """Prometheus-compatible metrics endpoint"""
    start_time = time.time()
    logger.info("Prometheus metrics request started")

    prometheus_data = request.app.state.app_state.metrics_collector.get_prometheus_metrics()

    response_time = time.time() - start_time
    data_size = len(prometheus_data) if prometheus_data else 0
    logger.info(
        "Prometheus metrics retrieved",
        response_time=response_time,
        data_size_bytes=data_size,
    )

    return Response(content=prometheus_data, media_type="text/plain; charset=utf-8")
