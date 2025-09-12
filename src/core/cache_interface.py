"""
Unified Cache Interface - Single Interface for All Cache Implementations

This module defines the unified cache interface that all cache implementations
must conform to, ensuring consistent behavior across the entire caching system.

Features:
- Defines standard cache operations (get, set, delete, clear)
- Supports both sync and async operations
- Includes metadata and statistics methods
- Category-based organization
- Extensible for future cache features
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Protocol
from datetime import datetime


class CacheEntry:
    """Standardized cache entry representation"""

    def __init__(
        self,
        key: str,
        value: Any,
        ttl: int = 300,
        category: str = "default",
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.category = category
        self.priority = priority
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0

    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl

    def touch(self) -> None:
        """Update last accessed time and increment access count"""
        self.last_accessed = datetime.now()
        self.access_count += 1


class CacheStats:
    """Standardized cache statistics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.evictions = 0
        self.expirations = 0
        self.total_requests = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate"""
        return self.hits / self.total_requests if self.total_requests > 0 else 0.0


class ICache(Protocol):
    """
    Unified Cache Interface Protocol

    All cache implementations must implement these methods to ensure
    consistent behavior across the caching system.
    """

    # Core cache operations
    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from cache"""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1
    ) -> bool:
        """Set value in cache"""
        ...

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        ...

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear cache entries, optionally by category"""
        ...

    async def has(self, key: str) -> bool:
        """Check if key exists in cache"""
        ...

    # Batch operations
    async def get_many(self, keys: List[str], category: str = "default") -> Dict[str, Any]:
        """Get multiple values from cache"""
        ...

    async def set_many(
        self,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        category: str = "default"
    ) -> int:
        """Set multiple values in cache"""
        ...

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from cache"""
        ...

    # TTL operations
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        ...

    async def ttl(self, key: str) -> int:
        """Get TTL for key (-1 if no TTL, -2 if key doesn't exist)"""
        ...

    # Statistics and monitoring
    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        ...

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get cache statistics (synchronous)"""
        ...

    # Category operations
    async def get_categories(self) -> List[str]:
        """Get all cache categories"""
        ...

    async def clear_category(self, category: str) -> int:
        """Clear all entries in a specific category"""
        ...

    # Maintenance operations
    async def cleanup_expired(self) -> int:
        """Remove expired entries"""
        ...

    async def optimize(self) -> Dict[str, Any]:
        """Optimize cache performance"""
        ...

    # Lifecycle operations
    async def start(self) -> None:
        """Start cache background tasks"""
        ...

    async def stop(self) -> None:
        """Stop cache background tasks"""
        ...

    def is_running(self) -> bool:
        """Check if cache is running"""
        ...


class ICacheWarmer(Protocol):
    """Cache Warmer Interface"""

    async def warm_key(self, key: str, getter_func: callable, priority: int = 1) -> bool:
        """Warm a specific key"""
        ...

    async def warm_category(self, category: str, priority: int = 1) -> Dict[str, Any]:
        """Warm all keys in a category"""
        ...

    def record_access(self, key: str, category: str = "default") -> None:
        """Record cache access for pattern analysis"""
        ...

    async def get_warming_stats(self) -> Dict[str, Any]:
        """Get warming statistics"""
        ...


class ICacheMonitor(Protocol):
    """Cache Monitor Interface"""

    async def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status"""
        ...

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Get detailed monitoring report"""
        ...

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get active alerts"""
        ...


# Factory functions for creating cache implementations
def create_memory_cache(**kwargs) -> ICache:
    """Create in-memory cache implementation"""
    from .memory_cache import MemoryCache
    return MemoryCache(**kwargs)


def create_disk_cache(**kwargs) -> ICache:
    """Create disk-backed cache implementation"""
    from .disk_cache import DiskCache
    return DiskCache(**kwargs)


def create_unified_cache(**kwargs) -> ICache:
    """Create unified cache implementation"""
    from .unified_cache import UnifiedCache
    return UnifiedCache(**kwargs)


# Global cache instances
_cache_instances: Dict[str, ICache] = {}


def get_cache_instance(name: str = "default", **kwargs) -> ICache:
    """Get or create named cache instance"""
    if name not in _cache_instances:
        _cache_instances[name] = create_unified_cache(**kwargs)

    return _cache_instances[name]


def clear_cache_instances() -> None:
    """Clear all cache instances"""
    global _cache_instances
    for cache in _cache_instances.values():
        asyncio.run(cache.stop())
    _cache_instances.clear()


# Utility functions
def generate_cache_key(*args, **kwargs) -> str:
    """Generate standardized cache key"""
    import hashlib
    key_parts = []

    for arg in args:
        if isinstance(arg, dict):
            key_parts.append(str(sorted(arg.items())))
        else:
            key_parts.append(str(arg))

    if kwargs:
        key_parts.append(str(sorted(kwargs.items())))

    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


async def get_or_set(
    cache: ICache,
    key: str,
    getter_func: callable,
    ttl: Optional[int] = None,
    category: str = "default"
) -> Any:
    """Get value from cache or set it using getter function"""
    value = await cache.get(key, category)
    if value is not None:
        return value

    value = await getter_func()
    await cache.set(key, value, ttl, category)
    return value


def cache_result(
    ttl: Optional[int] = None,
    category: str = "default",
    key_func: Optional[callable] = None
):
    """Decorator to cache function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_instance()

            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = generate_cache_key(func.__name__, args, kwargs)

            return await get_or_set(cache, key, lambda: func(*args, **kwargs), ttl, category)

        return wrapper
    return decorator