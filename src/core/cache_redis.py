import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import orjson
from redis.asyncio import Redis
from redis.exceptions import RedisError

from src.core.unified_config import RedisSettings

logger = logging.getLogger(__name__)

class RedisCacheAdapter:
    """
    A Redis-backed cache adapter that provides an interface compatible
    with other cache implementations in the system (e.g., SmartCache).
    """

    def __init__(self, settings: RedisSettings, default_ttl: int = 3600):
        self._redis: Optional[Redis] = None
        self._settings = settings
        self.default_ttl = default_ttl
        self.namespace = "llmproxy_cache"

        # Statistics
        self.hits = 0
        self.misses = 0
        self.total_requests = 0

    def _get_namespaced_key(self, key: str) -> str:
        """Construct a namespaced key for Redis."""
        return f"{self.namespace}:{key}"

    async def start(self):
        """Initialize the Redis connection."""
        if not self._settings.enabled:
            logger.info("Redis cache is disabled by configuration.")
            return

        if self._redis is not None:
            return

        try:
            self._redis = Redis(
                host=self._settings.host,
                port=self._settings.port,
                db=self._settings.db,
                password=self._settings.password,
                decode_responses=False  # We will handle decoding
            )
            await self._redis.ping()
            logger.info(
                f"Successfully connected to Redis at {self._settings.host}:{self._settings.port}"
            )
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis = None
            # Fallback or error handling can be implemented here
            raise ConnectionError(f"Could not connect to Redis: {e}") from e

    async def stop(self):
        """Close the Redis connection."""
        if self._redis:
            try:
                await self._redis.close()
                logger.info("Redis connection closed.")
            except RedisError as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if not self._redis:
            return None

        self.total_requests += 1
        namespaced_key = self._get_namespaced_key(key)

        try:
            cached_value = await self._redis.get(namespaced_key)
            if cached_value is None:
                self.misses += 1
                return None

            self.hits += 1
            # Deserialize the value from JSON
            return orjson.loads(cached_value)
        except RedisError as e:
            logger.error(f"Redis GET failed for key '{key}': {e}")
            return None
        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Redis for key '{key}': {e}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in the cache with a TTL."""
        if not self._redis:
            return False

        if ttl is None:
            ttl = self.default_ttl

        namespaced_key = self._get_namespaced_key(key)
        try:
            # Serialize the value to JSON
            serialized_value = orjson.dumps(value)
            await self._redis.set(namespaced_key, serialized_value, ex=ttl)
            return True
        except RedisError as e:
            logger.error(f"Redis SET failed for key '{key}': {e}")
            return False
        except TypeError as e:
            logger.error(f"Failed to serialize value for Redis for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from the cache."""
        if not self._redis:
            return False

        namespaced_key = self._get_namespaced_key(key)
        try:
            result = await self._redis.delete(namespaced_key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE failed for key '{key}': {e}")
            return False

    async def clear(self) -> bool:
        """Clear all keys within the cache's namespace."""
        if not self._redis:
            return False

        pattern = self._get_namespaced_key("*")
        try:
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
            logger.info(f"Cleared {len(keys)} keys from namespace '{self.namespace}'.")
            return True
        except RedisError as e:
            logger.error(f"Redis CLEAR (delete by pattern) failed: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self._redis:
            return {
                "backend": "redis",
                "enabled": False,
                "connected": False,
                "error": "Redis is not configured or connection failed.",
            }

        try:
            info = await self._redis.info()
            hit_rate = self.hits / self.total_requests if self.total_requests > 0 else 0
            return {
                "backend": "redis",
                "enabled": True,
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": info.get("db0", {}).get("keys", "N/A"),
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": self.total_requests,
                "hit_rate": round(hit_rate, 4),
            }
        except RedisError as e:
            logger.error(f"Failed to get Redis stats: {e}")
            return {
                "backend": "redis",
                "enabled": True,
                "connected": False,
                "error": str(e),
            }

    async def get_or_set(self, key: str, getter_func: callable, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set it using a getter function."""
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value

        new_value = await getter_func()
        await self.set(key, new_value, ttl=ttl)
        return new_value
