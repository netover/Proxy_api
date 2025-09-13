import time
from typing import Dict, Any

from fastapi import APIRouter, Request

from src.core.alerting import alert_manager
from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
from src.core.provider_factory import ProviderStatus
import asyncio
from src.core.rate_limiter import rate_limiter
from src.core.unified_config import ProviderConfig, config_manager
from src.core.provider_factory import provider_factory

logger = ContextualLogger(__name__)

router = APIRouter()


async def perform_parallel_health_checks(request: Request) -> Dict[str, Any]:
    """Perform health checks in parallel for better performance - PERFORMANCE OPTIMIZATION"""
    logger.info("Starting parallel health checks")

    # Get all providers
    config = request.app.state.app_state.config
    providers = config.providers

    async def check_provider_health(provider: ProviderConfig) -> Dict[str, Any]:
        """Check individual provider health"""
        try:
            provider_instance = await provider_factory.get_provider(provider.name)
            if not provider_instance:
                provider_instance = await provider_factory.create_provider(provider)

            if not provider_instance:
                return {
                    "name": provider.name,
                    "status": "error",
                    "error": "Failed to initialize provider"
                }

            # Quick health check
            start_time = time.time()
            result = await provider_instance.health_check()
            response_time = time.time() - start_time

            return {
                "name": provider.name,
                "status": "healthy" if result.get("healthy", False) else "unhealthy",
                "response_time": response_time,
                "details": result
            }
        except Exception as e:
            return {
                "name": provider.name,
                "status": "error",
                "error": str(e)
            }

    # Create tasks for parallel execution
    tasks = [check_provider_health(provider) for provider in providers]

    # Execute all health checks concurrently with timeout
    try:
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=30.0  # 30 second timeout for all checks
        )
    except asyncio.TimeoutError:
        logger.error("Parallel health checks timed out")
        results = [{"name": "timeout", "status": "error", "error": "Health check timeout"}]

    # Process results
    health_results = {}
    healthy_count = 0
    total_count = len(providers)

    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Health check task failed: {result}")
            continue

        health_results[result["name"]] = result
        if result["status"] == "healthy":
            healthy_count += 1

    logger.info(f"Parallel health checks completed: {healthy_count}/{total_count} providers healthy")

    return {
        "timestamp": time.time(),
        "total_providers": total_count,
        "healthy_providers": healthy_count,
        "unhealthy_providers": total_count - healthy_count,
        "providers": health_results
    }


@router.get("/health/providers")
@rate_limiter.limit(route="/health/providers")
async def provider_health_check(request: Request):
    """Deep health check of all providers in parallel"""
    return await perform_parallel_health_checks(request)

@router.get("/health")
@rate_limiter.limit(route="/v1/health")
async def health_check(request: Request):
    """Comprehensive health check with system monitoring"""
    start_time = time.time()
    logger.info("Health check request started")

    app_state = request.app.state.app_state
    provider_info = await app_state.provider_factory.get_all_provider_info()

    # Provider health summary
    healthy_count = sum(1 for p in provider_info
                        if p.status == ProviderStatus.HEALTHY)
    total_count = len(provider_info)
    overall_status = "healthy" if healthy_count > 0 else "unhealthy"

    # Get system metrics
    system_metrics = metrics_collector.get_all_stats()
    system_health = system_metrics.get("system_health", {})

    # Get active alerts
    active_alerts = alert_manager.get_active_alerts()
    critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
    warning_alerts = [a for a in active_alerts if a["severity"] == "warning"]

    # Determine overall health based on multiple factors
    health_score = 100

    # Provider health impact
    if total_count > 0:
        provider_health_ratio = healthy_count / total_count
        health_score -= (1 - provider_health_ratio) * 40  # 40% weight for providers

    # System resource impact
    cpu_percent = system_health.get("cpu_percent", 0)
    memory_percent = system_health.get("memory_percent", 0)
    disk_percent = system_health.get("disk_percent", 0)

    if cpu_percent > 90:
        health_score -= 20
    elif cpu_percent > 75:
        health_score -= 10

    if memory_percent > 90:
        health_score -= 20
    elif memory_percent > 80:
        health_score -= 10

    if disk_percent > 95:
        health_score -= 30
    elif disk_percent > 85:
        health_score -= 15

    # Alert impact
    if critical_alerts:
        health_score -= 30
    if warning_alerts:
        health_score -= 10

    # Ensure health score is within bounds
    health_score = max(0, min(100, health_score))

    # Determine status based on health score
    if health_score >= 80:
        overall_status = "healthy"
    elif health_score >= 60:
        overall_status = "degraded"
    elif health_score >= 30:
        overall_status = "unhealthy"
    else:
        overall_status = "critical"

    response_time = time.time() - start_time

    # Prepare comprehensive health response
    health_response = {
        "status": overall_status,
        "health_score": round(health_score, 1),
        "timestamp": time.time(),
        "response_time": round(response_time, 3),
        "version": "1.0.0",
        "uptime": system_metrics.get("uptime", 0),

        "providers": {
            "total": total_count,
            "healthy": healthy_count,
            "degraded": sum(1 for p in provider_info if p.status == ProviderStatus.DEGRADED),
            "unhealthy": sum(1 for p in provider_info if p.status == ProviderStatus.UNHEALTHY),
            "disabled": sum(1 for p in provider_info if p.status == ProviderStatus.DISABLED)
        },

        "system": {
            "cpu_percent": round(system_health.get("cpu_percent", 0), 1),
            "memory_percent": round(system_health.get("memory_percent", 0), 1),
            "memory_used_mb": round(system_health.get("memory_used_mb", 0), 1),
            "disk_percent": round(system_health.get("disk_percent", 0), 1),
            "network_connections": system_health.get("network_connections", 0),
            "threads_count": system_health.get("threads_count", 0)
        },

        "alerts": {
            "active": len(active_alerts),
            "critical": len(critical_alerts),
            "warning": len(warning_alerts),
            "recent": active_alerts[:5]  # Show last 5 alerts
        },

        "performance": {
            "total_requests": system_metrics.get("total_requests", 0),
            "successful_requests": system_metrics.get("successful_requests", 0),
            "failed_requests": system_metrics.get("failed_requests", 0),
            "overall_success_rate": round(system_metrics.get("overall_success_rate", 0) * 100, 1),
            "cache_hit_rate": round(system_metrics.get("cache_performance", {}).get("hit_rate", 0), 1),
            "avg_response_time": round(system_metrics.get("providers", {}).get("avg_response_time", 0), 3)
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

    logger.info("Health check completed",
               overall_status=overall_status,
               health_score=health_score,
               total_providers=total_count,
               healthy_providers=healthy_count,
               active_alerts=len(active_alerts),
               response_time=response_time)

    return health_response