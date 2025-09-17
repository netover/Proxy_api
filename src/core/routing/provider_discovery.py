"""
Provider Discovery Service for LLM Proxy API
Dynamic provider health monitoring and discovery system
"""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .logging import ContextualLogger
from .provider_factory import provider_factory
from .unified_cache import get_unified_cache

logger = ContextualLogger(__name__)


class ProviderHealth(Enum):
    """Provider health states for discovery"""

    EXCELLENT = "excellent"  # <100ms average, <0.1% error rate
    GOOD = "good"  # <300ms average, <1% error rate
    FAIR = "fair"  # <500ms average, <5% error rate
    POOR = "poor"  # <1000ms average, >5% error rate
    UNHEALTHY = "unhealthy"  # Unavailable or >10% error rate


@dataclass
class ProviderMetrics:
    """Real-time provider performance metrics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0.0
    last_request_time: float = 0.0
    error_rate_window: List[bool] = field(default_factory=list)
    latency_window: List[float] = field(default_factory=list)

    @property
    def average_latency(self) -> float:
        """Calculate average response time"""
        if not self.total_requests:
            return 0.0
        return self.total_latency_ms / self.total_requests

    @property
    def error_rate(self) -> float:
        """Calculate error rate from recent requests"""
        if not self.error_rate_window:
            return 0.0
        failed = sum(1 for result in self.error_rate_window if not result)
        return failed / len(self.error_rate_window)

    @property
    def health_score(self) -> ProviderHealth:
        """Calculate health score based on performance"""
        if self.total_requests == 0:
            return ProviderHealth.UNHEALTHY

        avg_latency = self.average_latency
        error_rate = self.error_rate * 100  # Convert to percentage

        if avg_latency < 100 and error_rate < 0.1:
            return ProviderHealth.EXCELLENT
        elif avg_latency < 300 and error_rate < 1:
            return ProviderHealth.GOOD
        elif avg_latency < 500 and error_rate < 5:
            return ProviderHealth.FAIR
        elif avg_latency < 1000 and error_rate < 10:
            return ProviderHealth.POOR
        else:
            return ProviderHealth.UNHEALTHY

    def record_request(self, success: bool, latency_ms: float):
        """Record a request result and latency"""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.total_latency_ms += latency_ms
        self.min_latency_ms = min(self.min_latency_ms, latency_ms)
        self.max_latency_ms = max(self.max_latency_ms, latency_ms)
        self.last_request_time = time.time()

        # Maintain rolling windows (last 100 requests)
        self.error_rate_window.append(success)
        self.latency_window.append(latency_ms)

        if len(self.error_rate_window) > 100:
            self.error_rate_window.pop(0)
        if len(self.latency_window) > 100:
            self.latency_window.pop(0)


@dataclass(order=True)
class ProviderPriority:
    """Priority queue element for provider selection"""

    priority: float
    provider_name: str
    metrics: ProviderMetrics = field(compare=False)


class ProviderDiscoveryService:
    """
    Advanced provider discovery and health monitoring service
    Enables dynamic provider selection based on real-time performance
    """

    def __init__(self):
        self._provider_metrics: Dict[str, ProviderMetrics] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._metrics_lock = asyncio.Lock()
        self._cache = None

        # Configuration
        self._health_check_interval = 30  # seconds
        self._metrics_ttl = 300  # 5 minutes
        self._min_requests_for_reliability = 10

        logger.info("Provider Discovery Service initialized")

    async def _get_cache(self):
        """Get or initialize the unified cache instance"""
        if self._cache is None:
            self._cache = await get_unified_cache()
        return self._cache

    def _generate_provider_cache_key(self, provider_name: str, data_type: str) -> str:
        """Generate cache key for provider data"""
        return f"provider:{provider_name}:{data_type}"

    async def start_monitoring(self):
        """Start background health monitoring"""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._health_check_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Started provider health monitoring")

    async def stop_monitoring(self):
        """Stop background health monitoring"""
        self._shutdown_event.set()

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped provider health monitoring")

    async def _health_monitoring_loop(self):
        """Background health monitoring loop"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_checks()
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self._health_check_interval,
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self._health_check_interval)

    async def _perform_health_checks(self):
        """Perform health checks on all providers"""
        provider_infos = await provider_factory.get_all_provider_info()

        for provider_info in provider_infos:
            try:
                provider = await provider_factory.get_provider(provider_info.name)
                if provider:
                    health_result = await provider.health_check()

                    # Record health check as a synthetic request
                    async with self._metrics_lock:
                        metrics = self._get_or_create_metrics(provider_info.name)
                        metrics.record_request(
                            success=health_result.get("healthy", False),
                            latency_ms=health_result.get("response_time", 0) * 1000,
                        )

            except Exception as e:
                logger.warning(f"Health check failed for {provider_info.name}: {e}")

                # Record failed health check
                async with self._metrics_lock:
                    metrics = self._get_or_create_metrics(provider_info.name)
                    metrics.record_request(success=False, latency_ms=5000)  # 5s timeout

    def _get_or_create_metrics(self, provider_name: str) -> ProviderMetrics:
        """Get or create metrics for a provider"""
        if provider_name not in self._provider_metrics:
            self._provider_metrics[provider_name] = ProviderMetrics()
        return self._provider_metrics[provider_name]

    async def record_request_result(
        self, provider_name: str, success: bool, latency_ms: float
    ):
        """Record the result of a real request"""
        async with self._metrics_lock:
            metrics = self._get_or_create_metrics(provider_name)
            metrics.record_request(success, latency_ms)

    def get_provider_metrics(self, provider_name: str) -> Optional[ProviderMetrics]:
        """Get metrics for a specific provider"""
        return self._provider_metrics.get(provider_name)

    def get_all_provider_metrics(self) -> Dict[str, ProviderMetrics]:
        """Get metrics for all providers"""
        return self._provider_metrics.copy()

    def get_provider_health(self, provider_name: str) -> ProviderHealth:
        """Get health status for a provider"""
        metrics = self._provider_metrics.get(provider_name)
        if not metrics or metrics.total_requests < self._min_requests_for_reliability:
            return ProviderHealth.UNHEALTHY
        return metrics.health_score

    def get_healthy_providers_for_model(self, model: str) -> List[str]:
        """
        Get healthy providers for a model, sorted by performance priority
        Returns providers in order of preference for parallel execution
        """
        # Get all providers that support the model
        candidate_providers = provider_factory._providers.keys()

        # Filter by model support and health
        healthy_providers = []
        for provider_name in candidate_providers:
            provider = provider_factory._providers[provider_name]
            if model in provider.models:
                health = self.get_provider_health(provider_name)
                if health in [
                    ProviderHealth.EXCELLENT,
                    ProviderHealth.GOOD,
                    ProviderHealth.FAIR,
                ]:
                    healthy_providers.append(provider_name)

        # Sort by performance score (lower is better)
        return sorted(healthy_providers, key=self._calculate_performance_score)

    def _calculate_performance_score(self, provider_name: str) -> float:
        """Calculate performance score for provider ordering"""
        metrics = self._provider_metrics.get(provider_name)
        if not metrics:
            return 999.0  # Very low priority for unknown providers

        # Score based on latency (lower better) and error rate (lower better)
        latency_score = metrics.average_latency / 1000.0  # Normalize to seconds
        error_score = metrics.error_rate * 10  # Weight errors higher

        return latency_score + error_score

    def get_best_provider_for_model(self, model: str) -> Optional[str]:
        """Get the single best provider for a model"""
        healthy_providers = self.get_healthy_providers_for_model(model)
        return healthy_providers[0] if healthy_providers else None

    async def get_provider_load_distribution(
        self,
    ) -> Dict[str, Dict[str, Any]]:
        """Get load distribution information for all providers with caching"""
        cache = await self._get_cache()
        cache_key = "provider:load_distribution:all"

        # Try to get from cache first
        cached_distribution = await cache.get(cache_key, category="providers")
        if cached_distribution is not None:
            return cached_distribution

        # Cache miss - compute distribution
        distribution = {}

        for provider_name, metrics in self._provider_metrics.items():
            if metrics.total_requests > 0:
                distribution[provider_name] = {
                    "total_requests": metrics.total_requests,
                    "success_rate": metrics.successful_requests
                    / metrics.total_requests,
                    "average_latency_ms": metrics.average_latency,
                    "error_rate": metrics.error_rate,
                    "health": metrics.health_score.value,
                    "last_request": metrics.last_request_time,
                }

        # Cache the result (10 minutes TTL for provider data)
        await cache.set(
            cache_key, distribution, ttl=600, category="providers", priority=2
        )

        return distribution

    async def reset_provider_metrics(self, provider_name: Optional[str] = None):
        """Reset metrics for a provider or all providers"""
        async with self._metrics_lock:
            if provider_name:
                if provider_name in self._provider_metrics:
                    self._provider_metrics[provider_name] = ProviderMetrics()
                    logger.info(f"Reset metrics for provider: {provider_name}")
            else:
                self._provider_metrics.clear()
                logger.info("Reset metrics for all providers")

    async def get_provider_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report with caching"""
        cache = await self._get_cache()
        cache_key = "provider:performance_report:all"

        # Try to get from cache first
        cached_report = await cache.get(cache_key, category="providers")
        if cached_report is not None:
            return cached_report

        # Cache miss - generate report
        report = {
            "timestamp": time.time(),
            "providers": {},
            "summary": {
                "total_providers": len(self._provider_metrics),
                "excellent_providers": 0,
                "good_providers": 0,
                "fair_providers": 0,
                "poor_providers": 0,
                "unhealthy_providers": 0,
            },
        }

        for provider_name, metrics in self._provider_metrics.items():
            health = metrics.health_score
            report["providers"][provider_name] = {
                "health": health.value,
                "total_requests": metrics.total_requests,
                "success_rate": round(
                    metrics.successful_requests / max(metrics.total_requests, 1),
                    4,
                ),
                "average_latency_ms": round(metrics.average_latency, 2),
                "error_rate": round(metrics.error_rate, 4),
                "last_request_time": metrics.last_request_time,
            }

            # Update summary counts
            if health == ProviderHealth.EXCELLENT:
                report["summary"]["excellent_providers"] += 1
            elif health == ProviderHealth.GOOD:
                report["summary"]["good_providers"] += 1
            elif health == ProviderHealth.FAIR:
                report["summary"]["fair_providers"] += 1
            elif health == ProviderHealth.POOR:
                report["summary"]["poor_providers"] += 1
            else:
                report["summary"]["unhealthy_providers"] += 1

        # Cache the result (5 minutes TTL for performance reports)
        await cache.set(cache_key, report, ttl=300, category="providers", priority=2)

        return report

    def should_retry_provider(self, provider_name: str, attempt: int) -> bool:
        """Determine if a provider should be retried based on performance"""
        metrics = self._provider_metrics.get(provider_name)
        if not metrics:
            return attempt < 3  # Default retry logic

        # Don't retry if error rate is too high
        if metrics.error_rate > 0.5:  # 50% error rate
            return False

        # Don't retry if average latency is too high
        if metrics.average_latency > 5000:  # 5 seconds
            return False

        # Standard retry logic
        return attempt < 3

    async def get_cache_stats(self):
        """Get cache statistics for provider discovery"""
        cache = await self._get_cache()
        stats = await cache.get_stats()

        # Filter stats for provider-related entries
        provider_entries = 0
        for category, count in stats.get("categories", {}).items():
            if category == "providers":
                provider_entries = count
                break

        return {
            "provider_cache_entries": provider_entries,
            "total_cache_entries": stats.get("entries", 0),
            "cache_hit_rate": stats.get("hit_rate", 0),
            "cache_memory_usage_mb": stats.get("memory_usage_mb", 0),
            "cache_max_memory_mb": stats.get("max_memory_mb", 0),
        }


# Global instance
provider_discovery = ProviderDiscoveryService()
