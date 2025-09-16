"""Unified Smart Cache System - Single Layer Cache Architecture

This module provides a unified cache system that combines the best features
of the existing dual cache system while eliminating complexity and synchronization risks.

Features:
- Single cache layer with smart TTL management
- Intelligent cache warming strategy
- Cache consistency monitoring and alerting
- Performance metrics and optimization
- Memory-aware LRU eviction
- Background cleanup and maintenance
- Thread-safe operations
- Multi-level caching (memory + disk)
- Dynamic TTL adjustment based on access patterns
"""

import asyncio
import hashlib
import json
import logging
import statistics
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

from .unified_config import config_manager

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata and access patterns"""

    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    average_access_time: float = 0.0
    category: str = "default"
    priority: int = 1  # 1=low, 5=high

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.timestamp > self.ttl

    def is_stale(self, stale_threshold: float = 0.8) -> bool:
        """Check if entry is stale (close to expiration)"""
        return time.time() - self.timestamp > (self.ttl * stale_threshold)

    def touch(self) -> None:
        """Update access statistics"""
        now = time.time()
        self.last_accessed = now
        self.access_count += 1
        self.hit_count += 1

    def record_miss(self) -> None:
        """Record a cache miss"""
        self.miss_count += 1

    def get_hit_rate(self) -> float:
        """Calculate hit rate for this entry"""
        total_requests = self.hit_count + self.miss_count
        return self.hit_count / total_requests if total_requests > 0 else 0.0

    def should_extend_ttl(
        self, min_accesses: int = 5, hit_rate_threshold: float = 0.7
    ) -> bool:
        """Determine if TTL should be extended based on usage patterns"""
        return (
            self.access_count >= min_accesses
            and self.get_hit_rate() >= hit_rate_threshold
        )


@dataclass
class CacheMetrics:
    """Comprehensive cache metrics"""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    sets: int = 0
    deletes: int = 0
    warmup_operations: int = 0
    consistency_checks: int = 0
    inconsistencies_found: int = 0
    memory_pressure_events: int = 0
    disk_operations: int = 0
    average_access_time: float = 0.0
    peak_memory_usage: int = 0
    categories: Dict[str, int] = field(default_factory=dict)


class UnifiedCache:
    """
    Unified Smart Cache System

    Combines the best features of ModelCache and SmartCache into a single,
    intelligent caching layer with advanced features.

    Key Features:
    - Dynamic TTL management based on access patterns
    - Multi-level caching (memory + optional disk)
    - Intelligent eviction policies
    - Background maintenance and optimization
    - Comprehensive metrics and monitoring
    - Category-based organization
    - Memory-aware operations
    - Consistency validation
    - Predictive warming
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: int = 1800,  # 30 minutes
        max_memory_mb: int = 512,
        enable_disk_cache: bool = True,
        cache_dir: Optional[Path] = None,
        cleanup_interval: int = 300,  # 5 minutes
        enable_smart_ttl: bool = True,
        enable_predictive_warming: bool = True,
        enable_consistency_monitoring: bool = True,
    ):
        # Core configuration
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.enable_disk_cache = enable_disk_cache
        self.enable_smart_ttl = enable_smart_ttl
        self.enable_predictive_warming = enable_predictive_warming
        self.enable_consistency_monitoring = enable_consistency_monitoring
        self.cleanup_interval = cleanup_interval

        # Cache storage
        self._memory_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Disk cache setup
        if enable_disk_cache:
            self.cache_dir = cache_dir or Path.cwd() / ".cache" / "unified"
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warming_task: Optional[asyncio.Task] = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        # Metrics and statistics
        self.metrics = CacheMetrics()
        self._access_times: List[float] = []
        self._category_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Predictive warming data
        self._access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self._popular_keys: Set[str] = set()
        self._warming_queue: asyncio.Queue = asyncio.Queue()

        logger.info(
            f"UnifiedCache initialized: max_size={max_size}, "
            f"default_ttl={default_ttl}s, memory_limit={max_memory_mb}MB, "
            f"disk_cache={enable_disk_cache}"
        )

    async def start(self) -> None:
        """Start background maintenance tasks"""
        if self._running:
            return

        self._running = True

        # Start background tasks
        tasks = []

        # Cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        tasks.append(self._cleanup_task)

        # Warming task
        if self.enable_predictive_warming:
            self._warming_task = asyncio.create_task(self._warming_loop())
            tasks.append(self._warming_task)

        # Monitoring task
        if self.enable_consistency_monitoring:
            self._monitoring_task = asyncio.create_task(
                self._monitoring_loop()
            )
            tasks.append(self._monitoring_task)

        logger.info("UnifiedCache background tasks started")

    async def stop(self) -> None:
        """Stop background maintenance tasks"""
        self._running = False

        tasks = []
        if self._cleanup_task:
            tasks.append(self._cleanup_task)
        if self._warming_task:
            tasks.append(self._warming_task)
        if self._monitoring_task:
            tasks.append(self._monitoring_task)

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        logger.info("UnifiedCache background tasks stopped")

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate consistent cache key from arguments"""
        key_parts = []

        for arg in args:
            if isinstance(arg, dict):
                key_parts.append(str(sorted(arg.items())))
            elif isinstance(arg, (list, tuple)):
                key_parts.append(str(arg))
            else:
                key_parts.append(str(arg))

        if kwargs:
            key_parts.append(str(sorted(kwargs.items())))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _estimate_size(self, obj: Any) -> int:
        """Estimate memory size of object in bytes"""
        if isinstance(obj, (str, bytes)):
            return len(obj)
        elif isinstance(obj, (list, tuple)):
            return sum(self._estimate_size(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(
                len(str(k)) + self._estimate_size(v) for k, v in obj.items()
            )
        else:
            return 256  # Rough estimate for other objects

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from cache with smart TTL management"""
        start_time = time.time()

        with self._lock:
            self.metrics.total_requests = (
                getattr(self.metrics, "total_requests", 0) + 1
            )

            if key not in self._memory_cache:
                self.metrics.misses += 1

                # Try loading from disk if enabled
                if self.enable_disk_cache:
                    entry = await self._load_from_disk(key)
                    if entry:
                        # Add to memory cache
                        self._memory_cache[key] = entry
                        self._memory_cache.move_to_end(key)
                        entry.touch()
                        self.metrics.hits += 1

                        access_time = time.time() - start_time
                        self._record_access_time(access_time)
                        return entry.value

                # Cache miss
                self._record_miss_pattern(key)
                return None

            entry = self._memory_cache[key]

            if entry.is_expired():
                # Remove expired entry
                del self._memory_cache[key]
                self.metrics.expirations += 1
                self.metrics.misses += 1

                # Try loading from disk
                if self.enable_disk_cache:
                    entry = await self._load_from_disk(key)
                    if entry and not entry.is_expired():
                        self._memory_cache[key] = entry
                        self._memory_cache.move_to_end(key)
                        entry.touch()
                        self.metrics.hits += 1

                        access_time = time.time() - start_time
                        self._record_access_time(access_time)
                        return entry.value

                return None

            # Check if TTL should be extended
            if self.enable_smart_ttl and entry.should_extend_ttl():
                entry.ttl = min(
                    entry.ttl * 2, self.default_ttl * 4
                )  # Cap at 4x default
                entry.timestamp = time.time()

            # Update access patterns
            entry.touch()
            self._memory_cache.move_to_end(key)
            self.metrics.hits += 1

            # Record access pattern for predictive warming
            self._record_access_pattern(key)

            access_time = time.time() - start_time
            self._record_access_time(access_time)

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1,
    ) -> bool:
        """Set value in cache with smart management"""
        if ttl is None:
            ttl = self.default_ttl

        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl,
            size_bytes=self._estimate_size(value),
            category=category,
            priority=priority,
        )

        with self._lock:
            # Check memory limits
            if not await self._check_memory_limit(entry.size_bytes):
                logger.warning("Cache memory limit exceeded, evicting entries")
                await self._enforce_memory_limit()
                self.metrics.memory_pressure_events += 1

            # Remove existing entry
            if key in self._memory_cache:
                del self._memory_cache[key]

            # Add new entry
            self._memory_cache[key] = entry
            self._memory_cache.move_to_end(key)

            # Update metrics
            self.metrics.sets += 1

            # Update category stats
            if category not in self.metrics.categories:
                self.metrics.categories[category] = 0
            self.metrics.categories[category] += 1

            # Save to disk if enabled
            if self.enable_disk_cache:
                await self._save_to_disk(entry)

            # Enforce size limits
            await self._enforce_size_limit()

            return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                self.metrics.deletes += 1

                # Remove from disk if enabled
                if self.enable_disk_cache:
                    await self._delete_from_disk(key)

                return True
            return False

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries, optionally by category"""
        with self._lock:
            if category:
                keys_to_remove = [
                    key
                    for key, entry in self._memory_cache.items()
                    if entry.category == category
                ]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                    if self.enable_disk_cache:
                        await self._delete_from_disk(key)
                return len(keys_to_remove)
            else:
                count = len(self._memory_cache)
                self._memory_cache.clear()

                # Clear disk cache if enabled
                if self.enable_disk_cache:
                    await self._clear_disk_cache()

                return count

    async def get_or_set(
        self,
        key: str,
        getter_func: callable,
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> Any:
        """Get value from cache or set it using getter function"""
        # Try to get from cache first
        value = await self.get(key, category)
        if value is not None:
            return value

        # Cache miss, call getter function
        value = await getter_func()

        # Cache the result
        await self.set(key, value, ttl, category)

        return value

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate entries matching a pattern"""
        with self._lock:
            keys_to_remove = [
                key for key in self._memory_cache.keys() if pattern in key
            ]

            for key in keys_to_remove:
                await self.delete(key)

            return len(keys_to_remove)

    async def warmup(
        self, keys: List[str], getter_func: callable
    ) -> Dict[str, Any]:
        """Warm up cache with specific keys"""
        results = {
            "total": len(keys),
            "successful": 0,
            "failed": 0,
            "errors": [],
        }

        for key in keys:
            try:
                # Add to warming queue for background processing
                await self._warming_queue.put((key, getter_func))
                results["successful"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"{key}: {str(e)}")

        self.metrics.warmup_operations += 1
        return results

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            current_memory = sum(
                entry.size_bytes for entry in self._memory_cache.values()
            )
            total_requests = getattr(self.metrics, "total_requests", 0)

            return {
                "entries": len(self._memory_cache),
                "max_size": self.max_size,
                "memory_usage_bytes": current_memory,
                "memory_usage_mb": round(current_memory / (1024 * 1024), 2),
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
                "hits": self.metrics.hits,
                "misses": self.metrics.misses,
                "total_requests": total_requests,
                "hit_rate": (
                    round(self.metrics.hits / total_requests, 4)
                    if total_requests > 0
                    else 0
                ),
                "evictions": self.metrics.evictions,
                "expirations": self.metrics.expirations,
                "sets": self.metrics.sets,
                "deletes": self.metrics.deletes,
                "warmup_operations": self.metrics.warmup_operations,
                "consistency_checks": self.metrics.consistency_checks,
                "inconsistencies_found": self.metrics.inconsistencies_found,
                "memory_pressure_events": self.metrics.memory_pressure_events,
                "disk_operations": self.metrics.disk_operations,
                "average_access_time": round(
                    self.metrics.average_access_time, 4
                ),
                "peak_memory_usage": self.metrics.peak_memory_usage,
                "categories": dict(self.metrics.categories),
                "cache_dir": (
                    str(self.cache_dir) if self.enable_disk_cache else None
                ),
                "smart_ttl_enabled": self.enable_smart_ttl,
                "predictive_warming_enabled": self.enable_predictive_warming,
                "consistency_monitoring_enabled": self.enable_consistency_monitoring,
            }

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
                await self._enforce_memory_limit()
                await self._optimize_ttl()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    async def _warming_loop(self) -> None:
        """Background warming loop"""
        while self._running:
            try:
                # Process warming queue
                if not self._warming_queue.empty():
                    key, getter_func = await self._warming_queue.get()
                    try:
                        value = await getter_func()
                        await self.set(key, value)
                        logger.debug(
                            f"Background warming completed for key: {key}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Background warming failed for key {key}: {e}"
                        )
                    finally:
                        self._warming_queue.task_done()

                await asyncio.sleep(1)  # Small delay to prevent busy waiting
            except Exception as e:
                logger.error(f"Cache warming error: {e}")

    async def _monitoring_loop(self) -> None:
        """Background consistency monitoring loop"""
        while self._running:
            try:
                await asyncio.sleep(
                    self.cleanup_interval * 2
                )  # Less frequent than cleanup
                await self._check_consistency()
                await self._update_popular_keys()
            except Exception as e:
                logger.error(f"Cache monitoring error: {e}")

    async def _cleanup_expired(self) -> None:
        """Remove expired entries"""
        with self._lock:
            expired_keys = [
                key
                for key, entry in self._memory_cache.items()
                if entry.is_expired()
            ]

            for key in expired_keys:
                del self._memory_cache[key]
                self.metrics.expirations += 1

            if expired_keys:
                logger.info(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )

    async def _enforce_size_limit(self) -> None:
        """Enforce maximum cache size using intelligent eviction"""
        with self._lock:
            while len(self._memory_cache) > self.max_size:
                # Evict based on priority and LRU
                candidates = list(self._memory_cache.items())

                # Sort by priority (lower priority first) then by last access
                candidates.sort(
                    key=lambda x: (x[1].priority, x[1].last_accessed)
                )

                key, entry = candidates[0]
                del self._memory_cache[key]
                self.metrics.evictions += 1

                logger.debug(
                    f"Evicted cache entry: {key} (priority: {entry.priority})"
                )

    async def _enforce_memory_limit(self) -> None:
        """Enforce memory limits by evicting least recently used items"""
        with self._lock:
            current_memory = sum(
                entry.size_bytes for entry in self._memory_cache.values()
            )

            if current_memory > self.max_memory_bytes:
                # Calculate target memory (80% of max)
                target_memory = int(self.max_memory_bytes * 0.8)
                memory_to_free = current_memory - target_memory

                freed_memory = 0
                evicted_count = 0

                # Evict items until we free enough memory
                while freed_memory < memory_to_free and self._memory_cache:
                    # Evict oldest accessed item
                    key, entry = self._memory_cache.popitem(last=False)
                    freed_memory += entry.size_bytes
                    evicted_count += 1
                    self.metrics.evictions += 1

                logger.info(
                    f"Memory limit enforced: freed {freed_memory} bytes, "
                    f"evicted {evicted_count} entries"
                )

    async def _check_memory_limit(self, additional_bytes: int) -> bool:
        """Check if adding additional bytes would exceed memory limit"""
        current_memory = sum(
            entry.size_bytes for entry in self._memory_cache.values()
        )
        return current_memory + additional_bytes <= self.max_memory_bytes

    async def _optimize_ttl(self) -> None:
        """Optimize TTL values based on access patterns"""
        if not self.enable_smart_ttl:
            return

        with self._lock:
            for entry in self._memory_cache.values():
                if entry.should_extend_ttl():
                    # Extend TTL for frequently accessed items
                    old_ttl = entry.ttl
                    entry.ttl = min(entry.ttl * 2, self.default_ttl * 4)
                    entry.timestamp = time.time()  # Reset expiration

                    if entry.ttl != old_ttl:
                        logger.debug(
                            f"Extended TTL for {entry.key}: {old_ttl}s -> {entry.ttl}s "
                            f"(hit_rate: {entry.get_hit_rate():.2f})"
                        )

    async def _check_consistency(self) -> None:
        """Check cache consistency between memory and disk"""
        if (
            not self.enable_disk_cache
            or not self.enable_consistency_monitoring
        ):
            return

        self.metrics.consistency_checks += 1

        with self._lock:
            inconsistencies = 0

            for key, entry in self._memory_cache.items():
                disk_entry = await self._load_from_disk(key, check_only=True)
                if disk_entry:
                    # Check if disk entry is different
                    if (
                        disk_entry.value != entry.value
                        or abs(disk_entry.timestamp - entry.timestamp) > 1
                    ):  # 1 second tolerance
                        inconsistencies += 1
                        logger.warning(
                            f"Cache inconsistency detected for key: {key}"
                        )

            if inconsistencies > 0:
                self.metrics.inconsistencies_found += inconsistencies
                logger.info(f"Found {inconsistencies} cache inconsistencies")

    async def _update_popular_keys(self) -> None:
        """Update list of popular keys for predictive warming"""
        with self._lock:
            # Find keys with high access frequency
            popular = [
                key
                for key, entry in self._memory_cache.items()
                if entry.access_count > 10 and entry.get_hit_rate() > 0.8
            ]

            self._popular_keys = set(popular[:100])  # Keep top 100

    def _record_access_time(self, access_time: float) -> None:
        """Record access time for performance monitoring"""
        self._access_times.append(access_time)

        # Keep only last 1000 measurements
        if len(self._access_times) > 1000:
            self._access_times = self._access_times[-1000:]

        # Update average
        if self._access_times:
            self.metrics.average_access_time = statistics.mean(
                self._access_times
            )

    def _record_access_pattern(self, key: str) -> None:
        """Record access pattern for predictive warming"""
        self._access_patterns[key].append(datetime.now())

        # Keep only recent patterns (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self._access_patterns[key] = [
            ts for ts in self._access_patterns[key] if ts > cutoff
        ]

    def _record_miss_pattern(self, key: str) -> None:
        """Record cache miss pattern"""
        # Could be used for predictive loading

    async def _load_from_disk(
        self, key: str, check_only: bool = False
    ) -> Optional[CacheEntry]:
        """Load entry from disk cache"""
        if not self.enable_disk_cache:
            return None

        try:
            cache_file = self.cache_dir / f"{key}.json"
            if not cache_file.exists():
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if check_only:
                # Just check if file exists and is readable
                return CacheEntry(
                    key=key,
                    value=None,
                    timestamp=data.get("timestamp", 0),
                    ttl=data.get("ttl", self.default_ttl),
                )

            # Full load
            entry = CacheEntry(
                key=key,
                value=data["value"],
                timestamp=data["timestamp"],
                ttl=data["ttl"],
                access_count=data.get("access_count", 0),
                category=data.get("category", "default"),
                priority=data.get("priority", 1),
            )

            self.metrics.disk_operations += 1
            return entry

        except Exception as e:
            logger.error(f"Error loading from disk cache for key {key}: {e}")
            return None

    async def _save_to_disk(self, entry: CacheEntry) -> None:
        """Save entry to disk cache"""
        if not self.enable_disk_cache:
            return

        try:
            cache_file = self.cache_dir / f"{entry.key}.json"
            data = {
                "key": entry.key,
                "value": entry.value,
                "timestamp": entry.timestamp,
                "ttl": entry.ttl,
                "access_count": entry.access_count,
                "category": entry.category,
                "priority": entry.priority,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.metrics.disk_operations += 1

        except Exception as e:
            logger.error(
                f"Error saving to disk cache for key {entry.key}: {e}"
            )

    async def _delete_from_disk(self, key: str) -> None:
        """Delete entry from disk cache"""
        if not self.enable_disk_cache:
            return

        try:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                cache_file.unlink()
                self.metrics.disk_operations += 1
        except Exception as e:
            logger.error(f"Error deleting from disk cache for key {key}: {e}")

    async def _clear_disk_cache(self) -> None:
        """Clear all disk cache files"""
        if not self.enable_disk_cache or not self.cache_dir.exists():
            return

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            self.metrics.disk_operations += 1
        except Exception as e:
            logger.error(f"Error clearing disk cache: {e}")


# Global unified cache instance
_unified_cache: Optional[UnifiedCache] = None


async def get_unified_cache() -> UnifiedCache:
    """Get the global unified cache instance"""
    global _unified_cache

    if _unified_cache is None:
        config = config_manager.load_config()

        # Configure cache based on unified config
        cache_config = getattr(config.settings, "cache", None)
        if cache_config:
            _unified_cache = UnifiedCache(
                max_size=getattr(cache_config, "max_size", 10000),
                default_ttl=getattr(cache_config, "default_ttl", 1800),
                max_memory_mb=getattr(cache_config, "max_memory_mb", 512),
                enable_disk_cache=getattr(
                    cache_config, "enable_disk_cache", True
                ),
                enable_smart_ttl=getattr(
                    cache_config, "enable_smart_ttl", True
                ),
                enable_predictive_warming=getattr(
                    cache_config, "enable_predictive_warming", True
                ),
                enable_consistency_monitoring=getattr(
                    cache_config, "enable_consistency_monitoring", True
                ),
            )
        else:
            # Default configuration
            _unified_cache = UnifiedCache()

        await _unified_cache.start()

    return _unified_cache


async def initialize_unified_cache() -> None:
    """Initialize the global unified cache"""
    await get_unified_cache()
    logger.info("Unified cache initialized")


async def shutdown_unified_cache() -> None:
    """Shutdown the global unified cache"""
    global _unified_cache

    if _unified_cache:
        await _unified_cache.stop()
        _unified_cache = None
        logger.info("Unified cache shutdown")
