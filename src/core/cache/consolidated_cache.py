"""
Consolidated Cache Manager - Single Unified Cache System

This module provides a consolidated cache manager that integrates all caching
functionality into a single, unified system implementing the ICache interface.

Features:
- Single cache instance for all use cases
- Category-based organization (models, responses, summaries, etc.)
- Integrated warming and monitoring
- Backward compatibility adapters
- Memory and disk persistence
- Performance optimization
"""

import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

from .cache_interface import CacheStats, ICache
from .cache_migration import CacheMigrationService
from .cache_monitor import CacheMonitor
from .cache_warmer import CacheWarmer
from .logging import ContextualLogger
from .unified_cache import get_unified_cache

logger = ContextualLogger(__name__)


class CacheTier(Enum):
    """Cache tier levels for data organization"""

    HOT = "hot"  # Frequently accessed, fast storage
    WARM = "warm"  # Moderately accessed, balanced storage
    COLD = "cold"  # Rarely accessed, cost-effective storage


class CacheCategory:
    """Predefined cache categories for better organization"""

    # Core data types
    MODELS = "models"
    RESPONSES = "responses"
    SUMMARIES = "summaries"
    METRICS = "metrics"

    # System categories
    CONFIG = "config"
    TOKENS = "tokens"
    SESSIONS = "sessions"

    # Performance categories
    QUERIES = "queries"
    RESULTS = "results"
    ANALYTICS = "analytics"

    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all predefined categories"""
        return [
            cls.MODELS,
            cls.RESPONSES,
            cls.SUMMARIES,
            cls.METRICS,
            cls.CONFIG,
            cls.TOKENS,
            cls.SESSIONS,
            cls.QUERIES,
            cls.RESULTS,
            cls.ANALYTICS,
        ]


class ConsolidatedCacheManager:
    """
    Consolidated Cache Manager - Single source of truth for all caching needs

    This manager provides:
    - Unified interface for all cache operations
    - Category-based cache organization
    - Integrated warming and monitoring
    - Automatic migration support
    - Performance optimization
    - Backward compatibility
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        enable_warming: bool = True,
        enable_monitoring: bool = True,
        enable_migration: bool = True,
        max_memory_mb: int = 512,
        default_ttl: int = 1800,
    ):
        self.cache_dir = cache_dir or Path.cwd() / ".cache" / "consolidated"
        self.enable_warming = enable_warming
        self.enable_monitoring = enable_monitoring
        self.enable_migration = enable_migration
        self.max_memory_mb = max_memory_mb
        self.default_ttl = default_ttl

        # Core components
        self._cache: Optional[ICache] = None
        self._warmer: Optional[CacheWarmer] = None
        self._monitor: Optional[CacheMonitor] = None
        self._migrator: Optional[CacheMigrationService] = None

        # State management
        self._running = False
        self._migrated = False
        self._lock = threading.RLock()

        # Statistics
        self._stats = CacheStats()
        self._start_time = datetime.now()

        logger.info("ConsolidatedCacheManager initialized")

    async def initialize(self) -> None:
        """Initialize all cache components"""
        with self._lock:
            if self._running:
                return

            try:
                # Initialize unified cache as the core
                self._cache = await get_unified_cache()

                # Configure cache with our settings
                if hasattr(self._cache, "_unified_cache"):
                    unified = self._cache._unified_cache
                    # Apply our configuration to the underlying unified cache
                    if hasattr(unified, "max_memory_bytes"):
                        unified.max_memory_bytes = self.max_memory_mb * 1024 * 1024
                    if hasattr(unified, "default_ttl"):
                        unified.default_ttl = self.default_ttl

                # Initialize warmer
                if self.enable_warming:
                    self._warmer = CacheWarmer(
                        cache=self._cache,
                        enable_pattern_analysis=True,
                        enable_predictive_warming=True,
                    )
                    await self._warmer.start()

                # Initialize monitor
                if self.enable_monitoring:
                    self._monitor = CacheMonitor(target_hit_rate=0.9, check_interval=60)
                    await self._monitor.start_monitoring()

                # Initialize migrator
                if self.enable_migration:
                    self._migrator = CacheMigrationService()

                self._running = True
                logger.info("ConsolidatedCacheManager fully initialized")

            except Exception as e:
                logger.error(f"Failed to initialize ConsolidatedCacheManager: {e}")
                await self._cleanup_on_error()
                raise

    async def _cleanup_on_error(self) -> None:
        """Cleanup resources on initialization error"""
        if self._warmer:
            await self._warmer.stop()
        if self._monitor:
            await self._monitor.stop_monitoring()
        if self._cache:
            await self._cache.stop()

    async def migrate_legacy_caches(self) -> Dict[str, Any]:
        """Migrate data from legacy cache systems"""
        if not self._migrator or not self._cache:
            return {"error": "Migration not available"}

        try:
            # Migrate from SmartCache global instances
            from .smart_cache import get_response_cache, get_summary_cache

            await get_response_cache()
            await get_summary_cache()

            results = await self._migrator.migrate_to_unified_cache(
                ["response_cache", "summary_cache"]
            )

            # Mark as migrated
            self._migrated = True

            logger.info(f"Legacy cache migration completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Legacy cache migration failed: {e}")
            return {"error": str(e)}

    # ICache interface implementation

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from cache"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        self._stats.total_requests += 1

        try:
            value = await self._cache.get(key, category)

            if value is not None:
                self._stats.hits += 1

                # Record access for warming
                if self._warmer:
                    self._warmer.record_access(key, category)
            else:
                self._stats.misses += 1

            return value

        except Exception as e:
            self._stats.misses += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1,
    ) -> bool:
        """Set value in cache"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            success = await self._cache.set(key, value, ttl, category, priority)
            if success:
                self._stats.sets += 1
            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            success = await self._cache.delete(key)
            if success:
                self._stats.deletes += 1
            return success

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.clear(category)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0

    async def has(self, key: str) -> bool:
        """Check if key exists"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.has(key)
        except Exception:
            return False

    async def get_many(
        self, keys: List[str], category: str = "default"
    ) -> Dict[str, Any]:
        """Get multiple values"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.get_many(keys, category)
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}

    async def set_many(
        self,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> int:
        """Set multiple values"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.set_many(key_value_pairs, ttl, category)
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return 0

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.delete_many(keys)
        except Exception as e:
            logger.error(f"Cache delete_many error: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.expire(key, ttl)
        except Exception:
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.ttl(key)
        except Exception:
            return -2

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Get core cache stats
            cache_stats = await self._cache.get_stats()

            # Add manager-specific stats
            manager_stats = {
                "manager_type": "consolidated_cache",
                "running": self._running,
                "migrated": self._migrated,
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "components": {
                    "cache": self._cache is not None,
                    "warmer": self._warmer is not None,
                    "monitor": self._monitor is not None,
                    "migrator": self._migrator is not None,
                },
                "manager_stats": {
                    "hits": self._stats.hits,
                    "misses": self._stats.misses,
                    "sets": self._stats.sets,
                    "deletes": self._stats.deletes,
                    "total_requests": self._stats.total_requests,
                    "hit_rate": self._stats.hit_rate,
                },
            }

            # Add warmer stats if available
            if self._warmer:
                try:
                    warmer_stats = await self._warmer.get_warming_stats()
                    manager_stats["warmer_stats"] = warmer_stats
                except Exception as e:
                    manager_stats["warmer_stats"] = {"error": str(e)}

            # Add monitor stats if available
            if self._monitor:
                try:
                    health = await self._monitor.get_cache_health_report()
                    manager_stats["monitor_stats"] = health
                except Exception as e:
                    manager_stats["monitor_stats"] = {"error": str(e)}

            # Combine all stats
            combined_stats = {**cache_stats, **manager_stats}
            return combined_stats

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get cache statistics synchronously"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_stats())
        finally:
            loop.close()

    async def get_categories(self) -> List[str]:
        """Get all cache categories"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.get_categories()
        except Exception:
            return []

    async def clear_category(self, category: str) -> int:
        """Clear all entries in a category"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.clear_category(category)
        except Exception:
            return 0

    async def cleanup_expired(self) -> int:
        """Cleanup expired entries"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            return await self._cache.cleanup_expired()
        except Exception:
            return 0

    async def optimize(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Run cache optimization
            cache_result = await self._cache.optimize()

            # Run warmer optimization if available
            warmer_result = {}
            if self._warmer:
                warmer_result = await self._warmer.optimize_warming_strategy()

            return {
                "cache_optimization": cache_result,
                "warmer_optimization": warmer_result,
            }

        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
            return {"error": str(e)}

    async def start(self) -> None:
        """Start cache manager"""
        await self.initialize()

    async def stop(self) -> None:
        """Stop cache manager"""
        with self._lock:
            if not self._running:
                return

            try:
                # Stop components
                if self._warmer:
                    await self._warmer.stop()
                if self._monitor:
                    await self._monitor.stop_monitoring()
                if self._cache:
                    await self._cache.stop()

                self._running = False
                logger.info("ConsolidatedCacheManager stopped")

            except Exception as e:
                logger.error(f"Error stopping ConsolidatedCacheManager: {e}")

    def is_running(self) -> bool:
        """Check if cache manager is running"""
        return self._running

    # Model-specific methods (for backward compatibility)

    async def get_models(
        self, provider_name: str, base_url: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached models for a provider (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.get(key, category="models")

    async def set_models(
        self, provider_name: str, base_url: str, models: List[Dict[str, Any]]
    ) -> bool:
        """Cache models for a provider (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.set(key, models, category="models")

    async def invalidate_models(self, provider_name: str, base_url: str) -> bool:
        """Invalidate cached models (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.delete(key)

    # Response-specific methods (for SmartCache compatibility)

    async def get_response(self, key: str) -> Optional[Any]:
        """Get cached response (SmartCache compatibility)"""
        return await self.get(key, category="responses")

    async def set_response(
        self, key: str, response: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache response (SmartCache compatibility)"""
        return await self.set(key, response, ttl, category="responses")

    # Summary-specific methods (for SmartCache compatibility)

    async def get_summary(self, key: str) -> Optional[Any]:
        """Get cached summary (SmartCache compatibility)"""
        return await self.get(key, category="summaries")

    async def set_summary(
        self, key: str, summary: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache summary (SmartCache compatibility)"""
        return await self.set(key, summary, ttl, category="summaries")

    # Warming methods

    async def warm_provider_models(
        self, provider_name: str, base_url: str, getter_func: Callable
    ) -> bool:
        """Warm cache with provider models"""
        if not self._warmer:
            return False

        key = f"models:{provider_name}:{base_url}"
        return await self._warmer.warm_key(key, getter_func, priority=2)

    # Monitoring methods

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health report"""
        if not self._monitor:
            return {"error": "Monitoring not enabled"}

        return await self._monitor.get_cache_health_report()

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Get detailed monitoring report"""
        if not self._monitor:
            return {"error": "Monitoring not enabled"}

        return await self._monitor.get_monitoring_report()


# Global instance
_cache_manager: Optional[ConsolidatedCacheManager] = None


async def get_consolidated_cache_manager() -> ConsolidatedCacheManager:
    """Get the global consolidated cache manager instance"""
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = ConsolidatedCacheManager()
        await _cache_manager.initialize()

    return _cache_manager


def get_consolidated_cache_manager_sync() -> ConsolidatedCacheManager:
    """Get the global consolidated cache manager instance (synchronous)"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(get_consolidated_cache_manager())
    finally:
        loop.close()


async def initialize_consolidated_cache() -> None:
    """Initialize the global consolidated cache manager"""
    await get_consolidated_cache_manager()
    logger.info("Consolidated cache initialized")


async def shutdown_consolidated_cache() -> None:
    """Shutdown the global consolidated cache manager"""
    global _cache_manager

    if _cache_manager:
        await _cache_manager.stop()
        _cache_manager = None
        logger.info("Consolidated cache shutdown")
