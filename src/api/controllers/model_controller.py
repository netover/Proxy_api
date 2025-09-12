from fastapi import APIRouter, Depends, Request
import time
from typing import List

from src.core.auth import verify_api_key
from src.core.rate_limiter import rate_limiter
from src.core.provider_factory import ProviderStatus
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.core.unified_config import config_manager
from src.core.provider_discovery import provider_discovery
from src.core.cache_monitor import cache_monitor
from src.core.logging import ContextualLogger
from ..model_endpoints import router as model_router  # Import the existing model endpoints

logger = ContextualLogger(__name__)

router = APIRouter()

# Include the existing model management endpoints
router.include_router(model_router)

@router.get("/models")
async def list_models(request: Request):
    """List all available models across providers with caching"""
    start_time = time.time()
    logger.info("Listing models request started")

    from src.core.unified_config import config_manager
    config = config_manager.load_config()

    models = []
    discovery_service = ModelDiscoveryService()

    for provider in config.providers:
        if provider.enabled:
            try:
                # Use cached model discovery
                provider_config = ProviderConfig(
                    name=provider.name,
                    base_url=provider.base_url,
                    api_key=provider.api_key,
                    organization=getattr(provider, 'organization', None)
                )

                discovered_models = await discovery_service.discover_models(provider_config)

                for model_info in discovered_models:
                    models.append({
                        "id": model_info.id,
                        "object": "model",
                        "created": int(model_info.created.timestamp()) if model_info.created else int(time.time()),
                        "owned_by": model_info.owned_by or provider.name,
                        "provider_type": provider.type.value,
                        "status": "available",
                        "enabled": provider.enabled,
                        "forced": provider.forced
                    })

                logger.debug("Discovered models from provider",
                           provider=provider.name,
                           model_count=len(discovered_models))

            except Exception as e:
                # Fallback to config models if discovery fails
                logger.warning("Model discovery failed, using cached config",
                             provider=provider.name,
                             error=str(e),
                             fallback_models=len(provider.models))

                for model in provider.models:
                    models.append({
                        "id": model,
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": provider.name,
                        "provider_type": provider.type.value,
                        "status": "cached",
                        "enabled": provider.enabled,
                        "forced": provider.forced
                    })

    return {
        "object": "list",
        "data": models
    }

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
                    "status": provider.status.value,
                    "enabled": provider.enabled,
                    "forced": provider.forced
                })

    response_time = time.time() - start_time
    logger.info("Models listing completed",
               model_count=len(models),
               provider_count=len(config.providers),
               response_time=response_time)

    return {
        "object": "list",
        "data": models
    }

@router.get("/providers")
async def list_providers(request: Request):
    """List all configured providers with detailed information and caching"""
    from src.core.unified_config import config_manager
    config = config_manager.load_config()

    # Get cached provider performance data
    performance_report = await provider_discovery.get_provider_performance_report()

    providers = []
    for p in config.providers:
        # Get health data from cached performance report
        provider_health = performance_report.get("providers", {}).get(p.name, {})

        providers.append({
            "name": p.name,
            "type": p.type.value,
            "status": provider_health.get("health", "unknown"),
            "models": p.models,
            "priority": p.priority,
            "enabled": p.enabled,
            "forced": p.forced,
            "last_health_check": provider_health.get("last_request_time"),
            "error_count": provider_health.get("error_rate", 0),
            "success_rate": provider_health.get("success_rate", 0),
            "average_latency_ms": provider_health.get("average_latency_ms", 0),
            "total_requests": provider_health.get("total_requests", 0)
        })

    return {
        "providers": providers,
        "summary": performance_report.get("summary", {})
    }

@router.get("/cache/stats")
async def get_cache_stats(request: Request):
    """Get comprehensive cache statistics for monitoring hit rates"""
    start_time = time.time()
    logger.info("Cache stats request started")

    from src.core.unified_cache import get_unified_cache

    cache = await get_unified_cache()
    cache_stats = await cache.get_stats()

    # Get model discovery cache stats
    model_service = ModelDiscoveryService()
    model_stats = await model_service.get_cache_stats()

    # Get provider discovery cache stats
    provider_stats = await provider_discovery.get_cache_stats()

    # Combine all stats
    combined_stats = {
        "unified_cache": cache_stats,
        "model_cache": model_stats,
        "provider_cache": provider_stats,
        "overall_hit_rate": cache_stats.get("hit_rate", 0),
        "total_cache_entries": cache_stats.get("entries", 0),
        "cache_memory_usage_mb": cache_stats.get("memory_usage_mb", 0),
        "cache_health": "healthy" if cache_stats.get("hit_rate", 0) >= 0.9 else "needs_attention"
    }

    response_time = time.time() - start_time
    logger.info("Cache stats retrieved",
               response_time=response_time,
               hit_rate=cache_stats.get("hit_rate", 0),
               total_entries=cache_stats.get("entries", 0))

    return combined_stats

@router.post("/cache/clear")
async def clear_cache(request: Request, category: str = None):
    """Clear cache entries, optionally by category"""
    start_time = time.time()
    logger.info("Cache clear request started", category=category or "all")

    from src.core.unified_cache import get_unified_cache

    cache = await get_unified_cache()
    if category:
        count = await cache.clear(category=category)
    else:
        count = await cache.clear()

    # Also clear model and provider specific caches
    model_service = ModelDiscoveryService()
    model_count = await model_service.clear_all_model_cache()

    response_time = time.time() - start_time
    logger.info("Cache clear completed",
               response_time=response_time,
               unified_cache_cleared=count,
               model_cache_cleared=model_count,
               category=category or "all")

    return {
        "message": f"Cleared {count} unified cache entries and {model_count} model cache entries",
        "unified_cache_cleared": count,
        "model_cache_cleared": model_count
    }

@router.get("/cache/health")
async def get_cache_health(request: Request):
    """Get cache health report with hit rate monitoring"""
    return await cache_monitor.get_cache_health_report()

@router.post("/cache/warmup")
async def warmup_cache(request: Request):
    """Perform cache warming to improve hit rates"""
    results = await cache_monitor.warmup_cache()
    return {
        "message": "Cache warming completed",
        "results": results
    }

@router.post("/cache/monitor/start")
async def start_cache_monitoring(request: Request):
    """Start cache monitoring"""
    await cache_monitor.start_monitoring()
    return {"message": "Cache monitoring started"}

@router.post("/cache/monitor/stop")
async def stop_cache_monitoring(request: Request):
    """Stop cache monitoring"""
    await cache_monitor.stop_monitoring()
    return {"message": "Cache monitoring stopped"}