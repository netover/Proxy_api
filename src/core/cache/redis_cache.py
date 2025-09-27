"""
Redis-backed Distributed Cache System

This module provides a distributed cache that works across multiple instances
using Redis as the backend storage with advanced features like compression,
serialization, and monitoring.
"""

import asyncio
import json
import pickle
import time
import zlib
from typing import Any, Dict, Optional, Tuple, Union
import redis.asyncio as redis

from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


class RedisCache:
    """
    Redis-backed distributed cache with compression and monitoring.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        ttl: int = 300,  # 5 minutes default
        max_size_mb: int = 100,
        compression_enabled: bool = True,
        namespace: str = "cache",
        key_prefix: str = "",
    ):
        self.redis_url = redis_url
        self.ttl = ttl
        self.max_size_mb = max_size_mb
        self.compression_enabled = compression_enabled
        self.namespace = namespace
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "evictions": 0
        }

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info(f"Redis cache initialized: {self.redis_url}")
            logger.info(f"Cache TTL: {self.ttl}s, Max size: {self.max_size_mb}MB")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    async def shutdown(self):
        """Shutdown the cache and cleanup resources."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache shutdown complete")

    def _make_key(self, key: str) -> str:
        """Generate a namespaced key."""
        if self.key_prefix:
            return f"{self.namespace}:{self.key_prefix}:{key}"
        return f"{self.namespace}:{key}"

    def _compress_data(self, data: Any) -> bytes:
        """Compress data if compression is enabled."""
        serialized = pickle.dumps(data)
        if self.compression_enabled:
            return zlib.compress(serialized)
        return serialized

    def _decompress_data(self, data: bytes) -> Any:
        """Decompress data if compression was used."""
        if self.compression_enabled:
            decompressed = zlib.decompress(data)
        else:
            decompressed = data
        return pickle.loads(decompressed)

    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if not self.redis_client:
            return None  # Redis not available

        cache_key = self._make_key(key)

        try:
            # Get raw data
            raw_data = await self.redis_client.get(cache_key)

            if raw_data is None:
                self._stats["misses"] += 1
                return None

            # Decompress and deserialize
            data_bytes = raw_data.encode('latin1') if isinstance(raw_data, str) else raw_data
            value = self._decompress_data(data_bytes)

            self._stats["hits"] += 1
            return value

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Custom TTL (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False  # Redis not available

        cache_key = self._make_key(key)
        expiry = ttl or self.ttl

        try:
            # Compress and serialize
            data_bytes = self._compress_data(value)

            # Check size limit
            size_mb = len(data_bytes) / (1024 * 1024)
            if size_mb > self.max_size_mb:
                logger.warning(f"Cache entry too large: {size_mb:.2f}MB > {self.max_size_mb}MB")
                return False

            # Set with expiry
            await self.redis_client.setex(cache_key, expiry, data_bytes.decode('latin1'))

            self._stats["sets"] += 1
            return True

        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.redis_client:
            return False  # Redis not available

        cache_key = self._make_key(key)

        try:
            result = await self.redis_client.delete(cache_key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.redis_client:
            return False  # Redis not available

        cache_key = self._make_key(key)

        try:
            return await self.redis_client.exists(cache_key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {cache_key}: {e}")
            return False

    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            await self.initialize()

        try:
            pattern = f"{self.namespace}:*"
            keys = await self.redis_client.keys(pattern)

            if keys:
                await self.redis_client.delete(*keys)

            logger.info(f"Cleared {len(keys)} cache entries")
            return True

        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            if not self.redis_client:
                await self.initialize()

            # Get Redis info
            info = await self.redis_client.info("memory")

            pattern = f"{self.namespace}:*"
            keys = await self.redis_client.keys(pattern)

            return {
                "redis_connected": True,
                "redis_memory_used": info.get("used_memory_human", "unknown"),
                "redis_memory_peak": info.get("used_memory_peak_human", "unknown"),
                "cache_entries": len(keys),
                "cache_ttl": self.ttl,
                "cache_max_size_mb": self.max_size_mb,
                "compression_enabled": self.compression_enabled,
                "stats": self._stats.copy()
            }

        except Exception as e:
            return {
                "redis_connected": False,
                "error": str(e),
                "stats": self._stats.copy()
            }

    async def get_ttl(self, key: str) -> int:
        """
        Get remaining TTL for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if key doesn't exist
        """
        if not self.redis_client:
            await self.initialize()

        cache_key = self._make_key(key)

        try:
            return await self.redis_client.ttl(cache_key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {cache_key}: {e}")
            return -1


class DistributedCacheManager:
    """
    Manager for multiple Redis cache instances with different purposes.
    """

    def __init__(self):
        self.caches: Dict[str, RedisCache] = {}
        self._initialized = False

    async def initialize(self, config):
        """Initialize all cache instances from configuration."""
        if self._initialized:
            return

        try:
            # Response cache
            if hasattr(config, 'response_cache'):
                response_config = config.response_cache
                self.caches['response'] = RedisCache(
                    redis_url=getattr(config, 'redis_url', 'redis://localhost:6379'),
                    ttl=response_config.ttl,
                    max_size_mb=response_config.max_size_mb,
                    compression_enabled=response_config.compression,
                    namespace='response_cache'
                )
                try:
                    await self.caches['response'].initialize()
                    logger.info("Response cache initialized")
                except Exception as e:
                    logger.warning(f"Response cache initialization failed: {e}")

            # Summary cache
            if hasattr(config, 'summary_cache'):
                summary_config = config.summary_cache
                self.caches['summary'] = RedisCache(
                    redis_url=getattr(config, 'redis_url', 'redis://localhost:6379'),
                    ttl=summary_config.ttl,
                    max_size_mb=summary_config.max_size_mb,
                    compression_enabled=summary_config.compression,
                    namespace='summary_cache'
                )
                try:
                    await self.caches['summary'].initialize()
                    logger.info("Summary cache initialized")
                except Exception as e:
                    logger.warning(f"Summary cache initialization failed: {e}")

            self._initialized = True
            logger.info(f"Distributed cache manager initialized with {len(self.caches)} caches")

        except Exception as e:
            logger.error(f"Failed to initialize distributed cache manager: {e}")
            raise

    async def shutdown(self):
        """Shutdown all cache instances."""
        for name, cache in self.caches.items():
            try:
                await cache.shutdown()
                logger.info(f"Cache {name} shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down cache {name}: {e}")

        self.caches.clear()
        self._initialized = False

    def get_cache(self, name: str) -> Optional[RedisCache]:
        """Get a specific cache instance."""
        return self.caches.get(name)

    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        stats = {}
        for name, cache in self.caches.items():
            stats[name] = await cache.get_stats()
        return stats


# Global instances
response_cache = None
summary_cache = None
cache_manager = None


def get_response_cache(config=None) -> RedisCache:
    """Get or create the response cache instance."""
    global response_cache
    if response_cache is None:
        response_cache = RedisCache(
            redis_url=getattr(config, 'redis_url', 'redis://localhost:6379') if config else 'redis://localhost:6379',
            ttl=getattr(config, 'ttl', 300) if config else 300,
            max_size_mb=getattr(config, 'max_size_mb', 100) if config else 100,
            compression_enabled=getattr(config, 'compression', True) if config else True,
            namespace='response_cache'
        )
    return response_cache


def get_summary_cache(config=None) -> RedisCache:
    """Get or create the summary cache instance."""
    global summary_cache
    if summary_cache is None:
        summary_cache = RedisCache(
            redis_url=getattr(config, 'redis_url', 'redis://localhost:6379') if config else 'redis://localhost:6379',
            ttl=getattr(config, 'ttl', 3600) if config else 3600,
            max_size_mb=getattr(config, 'max_size_mb', 50) if config else 50,
            compression_enabled=getattr(config, 'compression', True) if config else True,
            namespace='summary_cache'
        )
    return summary_cache


def get_cache_manager() -> DistributedCacheManager:
    """Get or create the cache manager instance."""
    global cache_manager
    if cache_manager is None:
        cache_manager = DistributedCacheManager()
    return cache_manager


async def shutdown_caches():
    """Shutdown all cache instances."""
    if cache_manager:
        await cache_manager.shutdown()
    if response_cache:
        await response_cache.shutdown()
    if summary_cache:
        await summary_cache.shutdown()
