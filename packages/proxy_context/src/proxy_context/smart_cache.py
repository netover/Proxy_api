"""
Smart Cache System for Production Use
Intelligent caching with TTL, size limits, and memory management.
"""

import asyncio
import time
import hashlib
from typing import Dict, Any, Optional, Union, List
from collections import OrderedDict
import logging
from dataclasses import dataclass, field
from threading import Lock

from .feature_flags import get_feature_flag_manager, is_feature_enabled

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata"""

    key: str
    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.timestamp > self.ttl

    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = time.time()
        self.access_count += 1


class SmartCache:
    """
    Production-ready cache with:
    - TTL (Time To Live) support
    - Size limits with LRU eviction
    - Memory usage monitoring
    - Cache statistics
    - Thread-safe operations
    - Intelligent key generation
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: int = 3600,  # 1 hour
        max_memory_mb: int = 512,
        cleanup_interval: int = 300,  # 5 minutes
        enable_compression: bool = True,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        self.enable_compression = enable_compression

        # Feature flag manager
        self._feature_manager = get_feature_flag_manager()

        # Apply feature flags to configuration
        if is_feature_enabled("smart_cache_memory_optimization"):
            # Increase memory limits with optimization enabled
            self.max_memory_bytes = int(self.max_memory_bytes * 1.5)
            logger.info("Smart cache memory optimization enabled")

        if is_feature_enabled("smart_cache_compression"):
            self.enable_compression = True
            logger.info("Smart cache compression enabled")
        else:
            self.enable_compression = False

        # Thread-safe storage
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0

        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start background cleanup task"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            "Smart cache started",
            extra={
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
            },
        )

    async def stop(self):
        """Stop background cleanup task"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Smart cache stopped")

    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
                await self._enforce_memory_limit()
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        # Convert args and kwargs to string representation
        key_parts = []

        for arg in args:
            if isinstance(arg, dict):
                # Sort dict keys for consistent hashing
                key_parts.append(str(sorted(arg.items())))
            else:
                key_parts.append(str(arg))

        if kwargs:
            key_parts.append(str(sorted(kwargs.items())))

        key_string = "|".join(key_parts)

        # Generate hash for consistent key length
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
            # Rough estimate for other objects
            return 256

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        start_time = (
            time.time()
            if is_feature_enabled("cache_performance_monitoring")
            else None
        )

        with self._lock:
            self.total_requests += 1

            if key not in self._cache:
                self.misses += 1
                if start_time:
                    logger.debug(
                        f"Cache miss for key: {key}, time: {time.time() - start_time:.6f}s"
                    )
                return None

            entry = self._cache[key]

            if entry.is_expired():
                # Remove expired entry
                del self._cache[key]
                self.misses += 1
                if start_time:
                    logger.debug(
                        f"Cache expired for key: {key}, time: {time.time() - start_time:.6f}s"
                    )
                return None

            # Update access statistics
            entry.touch()

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self.hits += 1

            if start_time:
                access_time = time.time() - start_time
                logger.debug(
                    f"Cache hit for key: {key}, time: {access_time:.6f}s"
                )

            return entry.value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        skip_memory_check: bool = False,
    ) -> bool:
        """Set value in cache"""
        if ttl is None:
            ttl = self.default_ttl

        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.time(),
            ttl=ttl,
            size_bytes=self._estimate_size(value),
        )

        with self._lock:
            # Check memory limits
            if not skip_memory_check and not await self._check_memory_limit(
                entry.size_bytes
            ):
                logger.warning(
                    "Cache memory limit exceeded, skipping cache set"
                )
                return False

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = entry
            self._cache.move_to_end(key)

            # Enforce size limits
            await self._enforce_size_limit()

            return True

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    async def _cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                logger.info(
                    f"Cleaned up {len(expired_keys)} expired cache entries"
                )

    async def _enforce_size_limit(self):
        """Enforce maximum cache size using LRU eviction"""
        with self._lock:
            while len(self._cache) > self.max_size:
                # Remove least recently used item
                key, entry = self._cache.popitem(last=False)
                self.evictions += 1

                logger.debug(f"Evicted cache entry: {key}")

    async def _enforce_memory_limit(self):
        """Enforce memory limits by evicting least recently used items"""
        with self._lock:
            current_memory = sum(
                entry.size_bytes for entry in self._cache.values()
            )

            if current_memory > self.max_memory_bytes:
                # Calculate how much memory to free (target 80% of max)
                target_memory = int(self.max_memory_bytes * 0.8)
                memory_to_free = current_memory - target_memory

                freed_memory = 0
                evicted_count = 0

                # Evict items until we free enough memory
                while freed_memory < memory_to_free and self._cache:
                    key, entry = self._cache.popitem(last=False)
                    freed_memory += entry.size_bytes
                    evicted_count += 1
                    self.evictions += 1

                logger.info(
                    "Memory limit enforced",
                    extra={
                        "freed_bytes": freed_memory,
                        "evicted_count": evicted_count,
                        "current_memory": current_memory - freed_memory,
                    },
                )

    async def _check_memory_limit(self, additional_bytes: int) -> bool:
        """Check if adding additional bytes would exceed memory limit"""
        current_memory = sum(
            entry.size_bytes for entry in self._cache.values()
        )
        return current_memory + additional_bytes <= self.max_memory_bytes

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_memory = sum(
                entry.size_bytes for entry in self._cache.values()
            )
            hit_rate = (
                self.hits / self.total_requests
                if self.total_requests > 0
                else 0
            )

            return {
                "entries": len(self._cache),
                "max_size": self.max_size,
                "memory_usage_bytes": current_memory,
                "memory_usage_mb": round(current_memory / (1024 * 1024), 2),
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024),
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": self.total_requests,
                "hit_rate": round(hit_rate, 4),
                "evictions": self.evictions,
                "default_ttl": self.default_ttl,
            }

    async def get_or_set(
        self, key: str, getter_func: callable, ttl: Optional[int] = None
    ) -> Any:
        """Get value from cache or set it using getter function"""
        # Try to get from cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Cache miss, call getter function
        value = await getter_func()

        # Cache the result
        await self.set(key, value, ttl)

        return value

    def generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments (synchronous)"""
        return self._generate_key(*args, **kwargs)


# Global cache instances
_response_cache: Optional[SmartCache] = None
_summary_cache: Optional[SmartCache] = None


async def get_response_cache() -> SmartCache:
    """Get global response cache instance"""
    global _response_cache

    if _response_cache is None:
        _response_cache = SmartCache(
            max_size=5000,  # Store more responses
            default_ttl=1800,  # 30 minutes
            max_memory_mb=256,
            cleanup_interval=600,  # 10 minutes
        )
        await _response_cache.start()

    return _response_cache


async def get_summary_cache() -> SmartCache:
    """Get global summary cache instance"""
    global _summary_cache

    if _summary_cache is None:
        _summary_cache = SmartCache(
            max_size=2000,  # Store fewer summaries (more expensive to generate)
            default_ttl=3600,  # 1 hour
            max_memory_mb=128,
            cleanup_interval=900,  # 15 minutes
        )
        await _summary_cache.start()

    return _summary_cache


async def initialize_caches():
    """Initialize all global caches"""
    await get_response_cache()
    await get_summary_cache()
    logger.info("All caches initialized")


async def shutdown_caches():
    """Shutdown all global caches"""
    global _response_cache, _summary_cache

    if _response_cache:
        await _response_cache.stop()
        _response_cache = None

    if _summary_cache:
        await _summary_cache.stop()
        _summary_cache = None

    logger.info("All caches shutdown")
