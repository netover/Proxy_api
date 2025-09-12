from fastapi import APIRouter, Request
import time

from src.core.provider_factory import ProviderStatus
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check(request: Request):
    """Comprehensive health check"""
    start_time = time.time()
    logger.info("Health check request started")

    app_state = request.app.state.app_state
    provider_info = await app_state.provider_factory.get_all_provider_info()

    healthy_count = sum(1 for p in provider_info
                        if p.status == ProviderStatus.HEALTHY)
    total_count = len(provider_info)

    overall_status = "healthy" if healthy_count > 0 else "unhealthy"

    response_time = time.time() - start_time
    logger.info("Health check completed",
               overall_status=overall_status,
               total_providers=total_count,
               healthy_providers=healthy_count,
               response_time=response_time)

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
                "enabled": p.enabled,
                "forced": p.forced,
                "last_check": p.last_health_check,
                "error_count": p.error_count
            }
            for p in provider_info
        ]
    }