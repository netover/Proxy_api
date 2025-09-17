"""
Consolidated Cache Manager - Enhanced Single Unified Cache System

This module provides an enhanced consolidated cache manager that integrates all caching
functionality into a single, unified system with advanced features.

Features:
- Single cache instance for all use cases
- Category-based organization (models, responses, summaries, metrics)
- Basic tiering logic (hot, warm, cold)
- Integrated warming and monitoring
- Backward compatibility adapters
- Memory and disk persistence
- Performance optimization
- Smart TTL management
"""

import asyncio
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

import redis.asyncio as redis

from .cache_interface import CacheStats, ICache
from .cache_migration import CacheMigrationService
from .cache_monitor import CacheMonitor
from .cache_warmer import CacheWarmer
from .logging import ContextualLogger
from .unified_cache import get_unified_cache

logger = ContextualLogger(__name__)


class DistributedLock:
    """
    A distributed lock implementation using Redis for cross-instance synchronization.
    This prevents multiple instances from performing the same work simultaneously (e.g., cache warming).
    """

    def __init__(self, redis_client: redis.Redis, lock_key: str, timeout: int = 30):
        """
        Initializes the distributed lock.
        Args:
            redis_client: An asynchronous Redis client instance.
            lock_key: The unique key for the lock.
            timeout: The lock's expiration time in seconds to prevent deadlocks.
        """
        self.redis = redis_client
        self.lock_key = f"lock:{lock_key}"
        self.timeout = timeout

    @asynccontextmanager
    async def __aenter__(self):
        """
        Acquires the lock, retrying with a backoff until it succeeds.
        Yields control once the lock is acquired.
        """
        # Continuously try to acquire the lock
        while not await self.redis.set(
            self.lock_key, "locked", nx=True, ex=self.timeout
        ):
            # If lock is not acquired, wait for a short period before retrying
            await asyncio.sleep(0.1)
        try:
            # Once the lock is acquired, yield to the context
            yield self
        finally:
            # Always release the lock upon exiting the context
            await self.redis.delete(self.lock_key)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Releases the lock when exiting the async with block."""
        await self.redis.delete(self.lock_key)


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
    Enhanced Consolidated Cache Manager - Single source of truth for all caching needs

    This manager provides:
    - Unified interface for all cache operations
    - Category-based cache organization
    - Basic tiering logic (hot/warm/cold)
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
        enable_tiering: bool = True,
        tier_thresholds: Optional[Dict[str, int]] = None,
        redis_url: Optional[str] = None,
    ):
        self.cache_dir = cache_dir or Path.cwd() / ".cache" / "consolidated"
        self.enable_warming = enable_warming
        self.enable_monitoring = enable_monitoring
        self.enable_migration = enable_migration
        self.max_memory_mb = max_memory_mb
        self.default_ttl = default_ttl
        self.enable_tiering = enable_tiering
        self.redis_url = redis_url or "redis://localhost"

        # Tier configuration
        self.tier_thresholds = tier_thresholds or {
            "hot_access_count": 10,  # Moves to hot tier after 10 accesses
            "warm_access_count": 3,  # Moves to warm tier after 3 accesses
            "cold_ttl_multiplier": 0.5,  # Cold tier has 50% shorter TTL
            "hot_ttl_multiplier": 2.0,  # Hot tier has 2x longer TTL
        }

        # Core components
        self._cache: Optional[ICache] = None
        self._warmer: Optional[CacheWarmer] = None
        self._monitor: Optional[CacheMonitor] = None
        self._migrator: Optional[CacheMigrationService] = None
        self.redis: Optional[redis.Redis] = None

        # Tier management
        self._tier_assignments: Dict[str, CacheTier] = {}
        self._category_tiers: Dict[str, CacheTier] = {}
        self._tier_stats: Dict[str, Dict[str, Any]] = {
            tier.value: {"entries": 0, "memory_usage": 0, "hit_rate": 0.0}
            for tier in CacheTier
        }

        # State management
        self._running = False
        self._migrated = False
        self._lock = threading.RLock()

        # Statistics
        self._stats = CacheStats()
        self._start_time = datetime.now()

        # Initialize category tiers (default assignments)
        self._initialize_category_tiers()

        logger.info("ConsolidatedCacheManager initialized with tiering support")

    def _initialize_category_tiers(self) -> None:
        """Initialize default tier assignments for categories"""
        # Models are typically hot (frequently accessed)
        self._category_tiers[CacheCategory.MODELS] = CacheTier.HOT

        # Responses are warm (moderately accessed)
        self._category_tiers[CacheCategory.RESPONSES] = CacheTier.WARM

        # Summaries and metrics are warm (analyzed periodically)
        self._category_tiers[CacheCategory.SUMMARIES] = CacheTier.WARM
        self._category_tiers[CacheCategory.METRICS] = CacheTier.WARM

        # Config and tokens are hot (critical system data)
        self._category_tiers[CacheCategory.CONFIG] = CacheTier.HOT
        self._category_tiers[CacheCategory.TOKENS] = CacheTier.HOT

        # Sessions are warm (user-specific, moderate access)
        self._category_tiers[CacheCategory.SESSIONS] = CacheTier.WARM

        # Queries and results are warm (query-dependent)
        self._category_tiers[CacheCategory.QUERIES] = CacheTier.WARM
        self._category_tiers[CacheCategory.RESULTS] = CacheTier.WARM

        # Analytics are cold (batch processing)
        self._category_tiers[CacheCategory.ANALYTICS] = CacheTier.COLD

    async def initialize(self) -> None:
        """Initialize all cache components"""
        with self._lock:
            if self._running:
                return

            try:
                # Initialize Redis client for distributed features
                self.redis = redis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
                await self.redis.ping()
                logger.info("Redis client connected successfully.")

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

    def _get_tier_for_category(self, category: str) -> CacheTier:
        """Get the assigned tier for a category"""
        return self._category_tiers.get(category, CacheTier.WARM)

    def _get_tier_for_key(self, key: str, category: str) -> CacheTier:
        """Get the tier for a specific key (considering dynamic tiering)"""
        if not self.enable_tiering:
            return self._get_tier_for_category(category)

        # Check if we have a dynamic assignment
        if key in self._tier_assignments:
            return self._tier_assignments[key]

        # Return category default
        return self._get_tier_for_category(category)

    def _calculate_tier_ttl(self, base_ttl: int, tier: CacheTier) -> int:
        """Calculate TTL based on tier"""
        if not self.enable_tiering:
            return base_ttl

        if tier == CacheTier.HOT:
            return int(base_ttl * self.tier_thresholds["hot_ttl_multiplier"])
        elif tier == CacheTier.COLD:
            return int(base_ttl * self.tier_thresholds["cold_ttl_multiplier"])
        else:  # WARM
            return base_ttl

    def _update_tier_assignment(
        self, key: str, category: str, access_count: int
    ) -> None:
        """Update tier assignment based on access patterns"""
        if not self.enable_tiering:
            return

        current_tier = self._tier_assignments.get(
            key, self._get_tier_for_category(category)
        )

        # Promote to higher tiers based on access count
        if (
            access_count >= self.tier_thresholds["hot_access_count"]
            and current_tier != CacheTier.HOT
        ):
            self._tier_assignments[key] = CacheTier.HOT
            logger.debug(f"Promoted key {key} to HOT tier")
        elif (
            access_count >= self.tier_thresholds["warm_access_count"]
            and current_tier == CacheTier.COLD
        ):
            self._tier_assignments[key] = CacheTier.WARM
            logger.debug(f"Promoted key {key} to WARM tier")

    # Core ICache interface implementation with tiering support

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from cache with tier-aware access"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        self._stats.total_requests += 1

        try:
            # Determine tier for this key
            tier = self._get_tier_for_key(key, category)

            value = await self._cache.get(key, category)

            if value is not None:
                self._stats.hits += 1

                # Update tier assignment based on access
                self._update_tier_assignment(
                    key, category, getattr(value, "access_count", 1)
                )

                # Record access for warming
                if self._warmer:
                    self._warmer.record_access(key, category)

                # Update tier statistics
                self._tier_stats[tier.value]["entries"] += 1

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
        """Set value in cache with tier-aware TTL calculation"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Determine tier and calculate tier-specific TTL
            tier = self._get_tier_for_key(key, category)
            effective_ttl = self._calculate_tier_ttl(ttl or self.default_ttl, tier)

            success = await self._cache.set(
                key, value, effective_ttl, category, priority
            )

            if success:
                self._stats.sets += 1
                # Update tier statistics
                self._tier_stats[tier.value]["entries"] += 1

            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Remove from tier assignments
            self._tier_assignments.pop(key, None)

            success = await self._cache.delete(key)
            if success:
                self._stats.deletes += 1
            return success

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries, optionally by category"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            count = await self._cache.clear(category)

            # Clear tier assignments for cleared entries
            if category:
                keys_to_remove = [
                    k
                    for k, t in self._tier_assignments.items()
                    if k.startswith(f"{category}:")
                ]
                for key in keys_to_remove:
                    del self._tier_assignments[key]

            return count
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
        """Set multiple values with tier-aware TTL"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Apply tiering to all keys
            tiered_pairs = {}
            for key, value in key_value_pairs.items():
                tier = self._get_tier_for_key(key, category)
                effective_ttl = self._calculate_tier_ttl(ttl or self.default_ttl, tier)
                tiered_pairs[key] = (value, effective_ttl)

            # Set with individual TTLs
            success_count = 0
            for key, (value, effective_ttl) in tiered_pairs.items():
                if await self._cache.set(key, value, effective_ttl, category):
                    success_count += 1
                    self._tier_stats[tier.value]["entries"] += 1

            self._stats.sets += success_count
            return success_count

        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return 0

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Remove from tier assignments
            for key in keys:
                self._tier_assignments.pop(key, None)

            count = await self._cache.delete_many(keys)
            self._stats.deletes += count
            return count

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
        """Get comprehensive cache statistics including tier information"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Get core cache stats
            cache_stats = await self._cache.get_stats()

            # Add manager-specific stats
            manager_stats = {
                "manager_type": "consolidated_cache_enhanced",
                "running": self._running,
                "migrated": self._migrated,
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "tiering_enabled": self.enable_tiering,
                "tier_assignments": len(self._tier_assignments),
                "tier_stats": self._tier_stats,
                "category_tiers": {
                    cat: tier.value for cat, tier in self._category_tiers.items()
                },
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
        """Get all cache categories including predefined ones"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            cache_categories = await self._cache.get_categories()
            # Add our predefined categories
            all_categories = set(cache_categories + CacheCategory.get_all_categories())
            return list(all_categories)
        except Exception:
            return CacheCategory.get_all_categories()

    async def clear_category(self, category: str) -> int:
        """Clear all entries in a category"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            count = await self._cache.clear_category(category)

            # Clear tier assignments for this category
            keys_to_remove = [
                k
                for k, t in self._tier_assignments.items()
                if k.startswith(f"{category}:")
            ]
            for key in keys_to_remove:
                del self._tier_assignments[key]

            return count
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
        """Optimize cache performance with tier-aware optimization"""
        if not self._cache:
            raise RuntimeError("Cache not initialized")

        try:
            # Run cache optimization
            cache_result = await self._cache.optimize()

            # Run tier optimization
            tier_result = await self._optimize_tiers()

            # Run warmer optimization if available
            warmer_result = {}
            if self._warmer:
                warmer_result = await self._warmer.optimize_warming_strategy()

            return {
                "cache_optimization": cache_result,
                "tier_optimization": tier_result,
                "warmer_optimization": warmer_result,
            }

        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
            return {"error": str(e)}

    async def _optimize_tiers(self) -> Dict[str, Any]:
        """Optimize tier assignments based on access patterns"""
        if not self.enable_tiering:
            return {"tiering_disabled": True}

        try:
            # Analyze access patterns and reassign tiers
            optimizations = {
                "reassigned_to_hot": 0,
                "reassigned_to_warm": 0,
                "reassigned_to_cold": 0,
                "total_analyzed": len(self._tier_assignments),
            }

            # This is a simplified optimization - in practice, you'd analyze
            # access patterns over time
            for key, tier in list(self._tier_assignments.items()):
                # Logic to reassign tiers based on recent activity
                # For now, just maintain current assignments
                pass

            return optimizations

        except Exception as e:
            logger.error(f"Tier optimization error: {e}")
            return {"error": str(e)}

    # Enhanced migration methods

    async def migrate_legacy_caches(self) -> Dict[str, Any]:
        """Migrate data from legacy cache systems with tier assignment"""
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

            # Assign appropriate tiers to migrated data
            if "response_cache" in results.get("migrated_caches", []):
                self._category_tiers[CacheCategory.RESPONSES] = CacheTier.WARM
            if "summary_cache" in results.get("migrated_caches", []):
                self._category_tiers[CacheCategory.SUMMARIES] = CacheTier.WARM

            # Mark as migrated
            self._migrated = True

            logger.info(f"Legacy cache migration completed: {results}")
            return results

        except Exception as e:
            logger.error(f"Legacy cache migration failed: {e}")
            return {"error": str(e)}

    # Enhanced warming methods

    async def warm_provider_models(
        self,
        provider_name: str,
        base_url: str,
        getter_func: Callable,
        priority: int = 2,
    ) -> bool:
        """Warm cache with provider models using tier-aware warming"""
        if not self._warmer:
            return False

        key = f"models:{provider_name}:{base_url}"
        tier = self._get_tier_for_category(CacheCategory.MODELS)

        # Use tier-specific priority
        if tier == CacheTier.HOT:
            priority = max(priority, 3)
        elif tier == CacheTier.COLD:
            priority = min(priority, 1)

        return await self._warmer.warm_key(key, getter_func, priority)

    async def warm_category(self, category: str, priority: int = 1) -> Dict[str, Any]:
        """Warm all keys in a category with tier awareness"""
        if not self._warmer:
            return {"error": "Warming not enabled"}

        try:
            tier = self._get_tier_for_category(category)

            # Adjust priority based on tier
            if tier == CacheTier.HOT:
                priority = max(priority, 3)
            elif tier == CacheTier.COLD:
                priority = min(priority, 1)

            return await self._warmer.warm_category(category, priority)

        except Exception as e:
            logger.error(f"Category warming error for {category}: {e}")
            return {"error": str(e)}

    async def warm_cache_batch(
        self, keys: List[str], getter_func: Callable, category: str, ttl: int
    ) -> Dict[str, Any]:
        """
        Warms a batch of keys in parallel, protected by a distributed lock to prevent race conditions.
        Args:
            keys: A list of keys to warm.
            getter_func: A callable that takes a key and returns the value to cache.
            category: The category to cache the items under.
            ttl: The time-to-live for the cached items.
        Returns:
            A dictionary with the status of the warming operation.
        """
        if not self._warmer or not self.redis:
            return {"error": "Warming or Redis not enabled"}

        # Use a hash of the sorted keys to uniquely identify this batch
        batch_id = hash(tuple(sorted(keys)))
        lock_key = f"warm_batch:{category}:{batch_id}"

        results = {
            "acquired_lock": False,
            "warmed_keys": 0,
            "failed_keys": 0,
            "errors": [],
        }

        try:
            lock = DistributedLock(self.redis, lock_key, timeout=60)
            async with lock:
                results["acquired_lock"] = True
                logger.info(f"Acquired distributed lock for warming batch {lock_key}")

                # Check which keys are not already in the cache
                existing_keys = await self.get_many(keys, category)
                keys_to_warm = [k for k in keys if k not in existing_keys]

                if not keys_to_warm:
                    logger.info(f"All keys in batch {lock_key} are already cached.")
                    return results

                async def _populate_cache(key: str):
                    try:
                        value = await getter_func(key)
                        await self.set(key, value, ttl, category)
                        return key, True
                    except Exception as e:
                        logger.error(
                            f"Failed to warm key {key} in batch {lock_key}: {e}"
                        )
                        return key, False

                tasks = [_populate_cache(key) for key in keys_to_warm]
                task_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in task_results:
                    if isinstance(result, Exception):
                        results["failed_keys"] += 1
                        results["errors"].append(str(result))
                    elif result[1]:
                        results["warmed_keys"] += 1
                    else:
                        results["failed_keys"] += 1

        except Exception as e:
            logger.error(
                f"Error during batch cache warming for {lock_key}: {e}",
                exc_info=True,
            )
            results["errors"].append(str(e))

        return results

    # Enhanced monitoring methods

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health report including tier information"""
        if not self._monitor:
            return {"error": "Monitoring not enabled"}

        try:
            health = await self._monitor.get_cache_health_report()

            # Add tier-specific health metrics
            health["tier_health"] = {}
            for tier_name, stats in self._tier_stats.items():
                tier_health = {
                    "entries": stats["entries"],
                    "memory_usage": stats["memory_usage"],
                    "hit_rate": stats["hit_rate"],
                    "status": (
                        "healthy" if stats["hit_rate"] > 0.5 else "needs_attention"
                    ),
                }
                health["tier_health"][tier_name] = tier_health

            return health

        except Exception as e:
            return {"error": str(e)}

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Get detailed monitoring report with tier analytics"""
        if not self._monitor:
            return {"error": "Monitoring not enabled"}

        try:
            report = await self._monitor.get_monitoring_report()

            # Add tier analytics
            report["tier_analytics"] = {
                "tier_distribution": {
                    tier: len(
                        [
                            k
                            for k, t in self._tier_assignments.items()
                            if t.value == tier
                        ]
                    )
                    for tier in [t.value for t in CacheTier]
                },
                "tier_performance": self._tier_stats,
                "category_tier_mapping": {
                    cat: tier.value for cat, tier in self._category_tiers.items()
                },
            }

            return report

        except Exception as e:
            return {"error": str(e)}

    # Lifecycle methods

    async def start(self) -> None:
        """Start cache manager with enhanced initialization"""
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
                if self.redis:
                    await self.redis.close()
                    logger.info("Redis client connection closed.")

                self._running = False
                logger.info("ConsolidatedCacheManager stopped")

            except Exception as e:
                logger.error(f"Error stopping ConsolidatedCacheManager: {e}")

    def is_running(self) -> bool:
        """Check if cache manager is running"""
        return self._running

    # Backward compatibility methods (enhanced)

    async def get_models(
        self, provider_name: str, base_url: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached models for a provider (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.get(key, category=CacheCategory.MODELS)

    async def set_models(
        self, provider_name: str, base_url: str, models: List[Dict[str, Any]]
    ) -> bool:
        """Cache models for a provider (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.set(key, models, category=CacheCategory.MODELS)

    async def invalidate_models(self, provider_name: str, base_url: str) -> bool:
        """Invalidate cached models (backward compatibility)"""
        key = f"models:{provider_name}:{base_url}"
        return await self.delete(key)

    async def get_response(self, key: str) -> Optional[Any]:
        """Get cached response (SmartCache compatibility)"""
        return await self.get(key, category=CacheCategory.RESPONSES)

    async def set_response(
        self, key: str, response: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache response (SmartCache compatibility)"""
        return await self.set(key, response, ttl, category=CacheCategory.RESPONSES)

    async def get_summary(self, key: str) -> Optional[Any]:
        """Get cached summary (SmartCache compatibility)"""
        return await self.get(key, category=CacheCategory.SUMMARIES)

    async def set_summary(
        self, key: str, summary: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache summary (SmartCache compatibility)"""
        return await self.set(key, summary, ttl, category=CacheCategory.SUMMARIES)

    # Enhanced utility methods

    def get_tier_info(self, category: str) -> Dict[str, Any]:
        """Get tier information for a category"""
        tier = self._get_tier_for_category(category)
        return {
            "category": category,
            "tier": tier.value,
            "ttl_multiplier": self.tier_thresholds.get(
                f"{tier.value}_ttl_multiplier", 1.0
            ),
            "access_threshold": self.tier_thresholds.get(
                f"{tier.value}_access_count", 0
            ),
        }

    async def rebalance_tiers(self) -> Dict[str, Any]:
        """Rebalance cache entries across tiers based on access patterns"""
        if not self.enable_tiering:
            return {"tiering_disabled": True}

        try:
            # Analyze current tier distribution and rebalance
            rebalance_stats = {
                "hot_tier_entries": len(
                    [k for k, t in self._tier_assignments.items() if t == CacheTier.HOT]
                ),
                "warm_tier_entries": len(
                    [
                        k
                        for k, t in self._tier_assignments.items()
                        if t == CacheTier.WARM
                    ]
                ),
                "cold_tier_entries": len(
                    [
                        k
                        for k, t in self._tier_assignments.items()
                        if t == CacheTier.COLD
                    ]
                ),
                "reassignments": 0,
            }

            # Simple rebalancing logic - could be enhanced
            # For now, just return current stats
            return rebalance_stats

        except Exception as e:
            logger.error(f"Tier rebalancing error: {e}")
            return {"error": str(e)}


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


# Enhanced migration utilities


async def migrate_cache_to_enhanced() -> Dict[str, Any]:
    """Migrate from basic ConsolidatedCacheManager to enhanced version"""
    try:
        # Get the current manager
        await get_consolidated_cache_manager()

        # Create enhanced manager
        ConsolidatedCacheManager()

        # Migrate data (simplified - in practice would need more sophisticated migration)
        migration_stats = {
            "source_manager": "ConsolidatedCacheManager",
            "target_manager": "EnhancedConsolidatedCacheManager",
            "status": "migration_simulated",
            "tiering_enabled": True,
            "categories_initialized": len(CacheCategory.get_all_categories()),
        }

        logger.info("Cache migration to enhanced version completed", migration_stats)
        return migration_stats

    except Exception as e:
        logger.error(f"Cache migration failed: {e}")
        return {"error": str(e)}


# Convenience functions for common operations


async def cache_model(
    provider_name: str, base_url: str, models: List[Dict[str, Any]]
) -> bool:
    """Convenience function to cache models"""
    manager = await get_consolidated_cache_manager()
    return await manager.set_models(provider_name, base_url, models)


async def get_cached_model(
    provider_name: str, base_url: str
) -> Optional[List[Dict[str, Any]]]:
    """Convenience function to get cached models"""
    manager = await get_consolidated_cache_manager()
    return await manager.get_models(provider_name, base_url)


async def cache_response(key: str, response: Any, ttl: Optional[int] = None) -> bool:
    """Convenience function to cache responses"""
    manager = await get_consolidated_cache_manager()
    return await manager.set_response(key, response, ttl)


async def get_cached_response(key: str) -> Optional[Any]:
    """Convenience function to get cached responses"""
    manager = await get_consolidated_cache_manager()
    return await manager.get_response(key)


async def get_cache_stats() -> Dict[str, Any]:
    """Convenience function to get cache statistics"""
    manager = await get_consolidated_cache_manager()
    return await manager.get_stats()
