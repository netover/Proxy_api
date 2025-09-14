import logging
from typing import Optional, Union

from src.core.cache_redis import RedisCacheAdapter
from src.core.smart_cache import SmartCache, get_response_cache, get_summary_cache
from src.core.unified_config import UnifiedConfig
from src.utils.context_condenser import AsyncLRUCache

logger = logging.getLogger(__name__)

# Define a unified cache interface type for type hinting
CacheInterface = Union[RedisCacheAdapter, SmartCache, AsyncLRUCache]

async def create_cache(config: UnifiedConfig, cache_name: str) -> CacheInterface:
    """
    Factory function to create and initialize a cache instance based on configuration.

    Args:
        config: The application's unified configuration.
        cache_name: The name of the cache to create ('response', 'summary', or 'lru').

    Returns:
        An initialized cache adapter instance.
    """
    redis_settings = getattr(config.settings, "redis", None)

    # Prioritize new redis block, fall back to old redis_url for condensation cache
    use_redis = False
    if redis_settings and redis_settings.enabled:
        use_redis = True
    elif cache_name == 'lru':
        # Backward compatibility for condensation cache
        redis_url = getattr(config.settings.condensation, 'cache_redis_url', None)
        if redis_url:
            logger.warning("Using deprecated 'cache_redis_url'. Please migrate to the top-level 'redis' config block.")
            use_redis = True
            # Populate redis_settings from url if not already set
            if not redis_settings or not redis_settings.enabled:
                from redis.connection import ConnectionPool
                pool = ConnectionPool.from_url(redis_url)
                redis_settings = pool.connection_kwargs
                # This is a simplification; a full conversion would be more complex.
                # For now, we assume a basic redis_url.
                from src.core.unified_config import RedisSettings
                redis_settings = RedisSettings(
                    enabled=True,
                    host=redis_settings.get('host', 'localhost'),
                    port=redis_settings.get('port', 6379),
                    db=redis_settings.get('db', 0),
                    password=redis_settings.get('password')
                )

    if use_redis and redis_settings:
        logger.info(f"Creating Redis cache for '{cache_name}'")
        # Use different namespaces for different caches in Redis
        if cache_name == 'response':
            ttl = getattr(config.settings.cache, 'response_cache', {}).get('ttl', 1800)
            adapter = RedisCacheAdapter(settings=redis_settings, default_ttl=ttl)
            adapter.namespace = "llmproxy_response"
        elif cache_name == 'summary':
            ttl = getattr(config.settings.cache, 'summary_cache', {}).get('ttl', 3600)
            adapter = RedisCacheAdapter(settings=redis_settings, default_ttl=ttl)
            adapter.namespace = "llmproxy_summary"
        else: # lru
            ttl = config.settings.condensation.cache_ttl
            adapter = RedisCacheAdapter(settings=redis_settings, default_ttl=ttl)
            adapter.namespace = "llmproxy_lru"

        await adapter.start()
        return adapter

    # Fallback to in-memory caches
    logger.info(f"Creating in-memory cache for '{cache_name}'")
    if cache_name == 'response':
        return await get_response_cache()
    elif cache_name == 'summary':
        return await get_summary_cache()
    else:  # lru
        persist_file = 'cache.json' if config.settings.condensation.cache_persist else None
        lru_cache = AsyncLRUCache(
            maxsize=config.settings.condensation.cache_size,
            persist_file=persist_file,
            redis_url=None  # Ensure it doesn't try to connect to Redis
        )
        await lru_cache.initialize()
        return lru_cache

async def shutdown_cache(cache: CacheInterface):
    """
    Shuts down a cache instance regardless of its type.
    """
    if isinstance(cache, RedisCacheAdapter):
        await cache.stop()
    elif isinstance(cache, SmartCache):
        # SmartCache shutdown is handled globally by shutdown_caches()
        # We can make this more robust later if needed.
        pass
    elif isinstance(cache, AsyncLRUCache):
        await cache.shutdown()
