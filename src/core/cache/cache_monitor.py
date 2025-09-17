"""
Cache Monitor Service for ProxyAPI
Monitors cache performance and ensures hit rates meet targets
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .logging import ContextualLogger
from .metrics import metrics_collector
from .model_discovery import ModelDiscoveryService
from .provider_discovery import provider_discovery
from .unified_cache import get_unified_cache
from src.providers.registry import ProviderConfig

logger = ContextualLogger(__name__)


@dataclass
class CacheAlert:
    """Cache performance alert"""

    alert_type: str
    message: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    timestamp: float
    hit_rate: float
    target_hit_rate: float = 0.9


class CacheMonitor:
    """
    Monitors cache performance and provides alerts when hit rates drop below targets.

    Features:
    - Continuous monitoring of cache hit rates
    - Alert generation for performance issues
    - Cache warming suggestions
    - Performance reporting
    """

    def __init__(self, target_hit_rate: float = 0.9, check_interval: int = 60):
        self.target_hit_rate = target_hit_rate
        self.check_interval = check_interval
        self._cache = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        self._alerts: List[CacheAlert] = []
        self._last_check_time = 0

    async def start_monitoring(self):
        """Start cache monitoring"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Cache monitor started", target_hit_rate=self.target_hit_rate)

    async def stop_monitoring(self):
        """Stop cache monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache monitor stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                await self._check_cache_performance()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Cache monitoring error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_cache_performance(self):
        """Check cache performance and generate alerts if needed"""
        try:
            cache = await self._get_cache()
            stats = await cache.get_stats()

            hit_rate = stats.get("hit_rate", 0)
            self._last_check_time = time.time()

            # Update metrics collector with cache performance data
            metrics_collector.update_cache_metrics(stats)

            # Check if hit rate is below target
            if hit_rate < self.target_hit_rate:
                severity = self._calculate_severity(hit_rate)
                alert = CacheAlert(
                    alert_type="low_hit_rate",
                    message=f"Cache hit rate {hit_rate:.2%} below target {self.target_hit_rate:.2%}",
                    severity=severity,
                    timestamp=time.time(),
                    hit_rate=hit_rate,
                    target_hit_rate=self.target_hit_rate,
                )
                self._alerts.append(alert)
                logger.warning(
                    "Cache performance alert",
                    message=alert.message,
                    hit_rate=alert.hit_rate,
                    target_hit_rate=alert.target_hit_rate,
                    severity=alert.severity,
                )

                # Log additional cache statistics
                logger.info(
                    f"Cache stats - Entries: {stats.get('entries', 0)}, "
                    f"Memory: {stats.get('memory_usage_mb', 0)}MB, "
                    f"Evictions: {stats.get('evictions', 0)}"
                )

            # Clean old alerts (keep last 100)
            if len(self._alerts) > 100:
                self._alerts = self._alerts[-100:]

        except Exception as e:
            logger.error(f"Error checking cache performance: {e}")

    def _calculate_severity(self, hit_rate: float) -> str:
        """Calculate alert severity based on hit rate"""
        diff = self.target_hit_rate - hit_rate

        if diff >= 0.3:  # 30% below target
            return "critical"
        elif diff >= 0.2:  # 20% below target
            return "high"
        elif diff >= 0.1:  # 10% below target
            return "medium"
        else:
            return "low"

    async def _get_cache(self):
        """Get or initialize cache instance"""
        if self._cache is None:
            self._cache = await get_unified_cache()
        return self._cache

    async def get_cache_health_report(self) -> Dict[str, Any]:
        """Get comprehensive cache health report"""
        cache = await self._get_cache()
        stats = await cache.get_stats()

        # Get model and provider cache stats
        model_service = ModelDiscoveryService()
        model_stats = await model_service.get_cache_stats()

        provider_stats = await provider_discovery.get_cache_stats()

        hit_rate = stats.get("hit_rate", 0)
        health_status = "healthy" if hit_rate >= self.target_hit_rate else "unhealthy"

        report = {
            "timestamp": time.time(),
            "overall_health": health_status,
            "target_hit_rate": self.target_hit_rate,
            "current_hit_rate": hit_rate,
            "hit_rate_percentage": round(hit_rate * 100, 2),
            "cache_stats": stats,
            "model_cache_stats": model_stats,
            "provider_cache_stats": provider_stats,
            "active_alerts": len(
                [a for a in self._alerts if time.time() - a.timestamp < 3600]
            ),  # Last hour
            "recent_alerts": [
                {
                    "type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp,
                    "hit_rate": alert.hit_rate,
                }
                for alert in self._alerts[-10:]  # Last 10 alerts
            ],
            "recommendations": self._generate_recommendations(hit_rate, stats),
        }

        return report

    def _generate_recommendations(
        self, hit_rate: float, stats: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on cache performance"""
        recommendations = []

        if hit_rate < self.target_hit_rate:
            recommendations.append(
                f"Cache hit rate is {hit_rate:.2%}, below target {self.target_hit_rate:.2%}"
            )

            if stats.get("evictions", 0) > 100:
                recommendations.append(
                    "High eviction rate detected - consider increasing cache size"
                )

            memory_usage = stats.get("memory_usage_mb", 0)
            max_memory = stats.get("max_memory_mb", 0)
            if memory_usage > max_memory * 0.9:
                recommendations.append(
                    "Cache memory usage is high - consider increasing memory limit"
                )

        if stats.get("entries", 0) < 10:
            recommendations.append(
                "Cache has very few entries - ensure cache warming is working"
            )

        return recommendations

    async def warmup_cache(self) -> Dict[str, Any]:
        """Perform cache warming to improve hit rates"""
        start_time = time.time()
        logger.info("Starting cache warming process")

        results = {"models_warmed": 0, "providers_warmed": 0, "errors": []}

        try:
            # Warm model cache
            model_service = ModelDiscoveryService()
            from src.core.unified_config import config_manager

            config = config_manager.load_config()

            for provider in config.providers:
                if provider.enabled:
                    try:
                        provider_config = ProviderConfig(
                            name=provider.name,
                            base_url=provider.base_url,
                            api_key=provider.api_key,
                            organization=getattr(provider, "organization", None),
                        )
                        await model_service.discover_models(provider_config)
                        results["models_warmed"] += 1
                    except Exception as e:
                        results["errors"].append(
                            f"Model warming failed for {provider.name}: {e}"
                        )

            # Warm provider cache
            await provider_discovery.get_provider_performance_report()
            results["providers_warmed"] = 1

            response_time = time.time() - start_time
            logger.info(
                "Cache warming completed",
                response_time=response_time,
                models_warmed=results.get("models_warmed", 0),
                providers_warmed=results.get("providers_warmed", 0),
                errors=len(results.get("errors", [])),
            )

        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            results["errors"].append(f"Cache warming failed: {e}")

        return results


# Global cache monitor instance
cache_monitor = CacheMonitor(target_hit_rate=0.9)
