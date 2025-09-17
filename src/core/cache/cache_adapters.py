"""
Cache Adapters - Adapter Pattern Implementation for Existing Cache Systems

This module provides adapter classes that wrap existing cache implementations
to conform to the unified cache interface, enabling seamless integration
and migration.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .cache_interface import CacheStats, ICache

logger = logging.getLogger(__name__)


class ModelCacheAdapter:
    """
    Adapter for ModelCache to implement unified cache interface

    Adapts the synchronous ModelCache to the async unified interface
    while maintaining backward compatibility.
    """

    def __init__(self, model_cache):
        self.model_cache = model_cache
        self._stats = CacheStats()
        self._running = False

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from model cache with unified interface"""
        self._stats.total_requests += 1

        try:
            if hasattr(self.model_cache, "get_models"):
                # This is a ModelCache instance
                if ":" in key:
                    # Parse provider:base_url format
                    parts = key.split(":", 1)
                    if len(parts) == 2:
                        provider_name, base_url = parts
                        result = self.model_cache.get_models(provider_name, base_url)
                        if result is not None:
                            self._stats.hits += 1
                            return result

            self._stats.misses += 1
            return None

        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter get for key {key}: {e}")
            self._stats.misses += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1,
    ) -> bool:
        """Set value in model cache with unified interface"""
        try:
            if hasattr(self.model_cache, "set_models"):
                # This is a ModelCache instance
                if ":" in key:
                    # Parse provider:base_url format
                    parts = key.split(":", 1)
                    if len(parts) == 2:
                        provider_name, base_url = parts
                        self.model_cache.set_models(provider_name, base_url, value)
                        self._stats.sets += 1
                        return True

            return False

        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter set for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from model cache"""
        try:
            if hasattr(self.model_cache, "invalidate"):
                if ":" in key:
                    parts = key.split(":", 1)
                    if len(parts) == 2:
                        provider_name, base_url = parts
                        result = self.model_cache.invalidate(provider_name, base_url)
                        if result:
                            self._stats.deletes += 1
                        return result
            return False
        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter delete for key {key}: {e}")
            return False

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear model cache"""
        try:
            if hasattr(self.model_cache, "invalidate_all"):
                count = self.model_cache.invalidate_all()
                return count
            return 0
        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter clear: {e}")
            return 0

    async def has(self, key: str) -> bool:
        """Check if key exists in model cache"""
        try:
            if ":" in key:
                parts = key.split(":", 1)
                if len(parts) == 2:
                    provider_name, base_url = parts
                    return self.model_cache.is_valid(provider_name, base_url)
            return False
        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter has for key {key}: {e}")
            return False

    async def get_many(
        self, keys: List[str], category: str = "default"
    ) -> Dict[str, Any]:
        """Get multiple values from model cache"""
        results = {}
        for key in keys:
            value = await self.get(key, category)
            if value is not None:
                results[key] = value
        return results

    async def set_many(
        self,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> int:
        """Set multiple values in model cache"""
        success_count = 0
        for key, value in key_value_pairs.items():
            if await self.set(key, value, ttl, category):
                success_count += 1
        return success_count

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from model cache"""
        success_count = 0
        for key in keys:
            if await self.delete(key):
                success_count += 1
        return success_count

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key (not supported by ModelCache)"""
        return False  # ModelCache doesn't support TTL changes

    async def ttl(self, key: str) -> int:
        """Get TTL for key (not supported by ModelCache)"""
        return -1  # ModelCache doesn't expose TTL info

    async def get_stats(self) -> Dict[str, Any]:
        """Get model cache statistics"""
        try:
            model_stats = self.model_cache.get_stats()
            return {
                "type": "model_cache_adapter",
                "model_cache_stats": model_stats,
                "adapter_stats": {
                    "hits": self._stats.hits,
                    "misses": self._stats.misses,
                    "sets": self._stats.sets,
                    "deletes": self._stats.deletes,
                    "hit_rate": self._stats.hit_rate,
                    "total_requests": self._stats.total_requests,
                },
            }
        except Exception as e:
            logger.error(
                f"Error during ModelCacheAdapter get_stats: {e}", exc_info=True
            )
            return {"error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get cache statistics synchronously"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_stats())
        finally:
            loop.close()

    async def get_categories(self) -> List[str]:
        """Get cache categories (ModelCache doesn't support categories)"""
        return ["models"]  # ModelCache is primarily for model data

    async def clear_category(self, category: str) -> int:
        """Clear category (not supported by ModelCache)"""
        return 0

    async def cleanup_expired(self) -> int:
        """Cleanup expired entries"""
        try:
            if hasattr(self.model_cache, "cleanup_expired"):
                return self.model_cache.cleanup_expired()
            return 0
        except Exception as e:
            logger.warning(f"Error during ModelCacheAdapter cleanup_expired: {e}")
            return 0

    async def optimize(self) -> Dict[str, Any]:
        """Optimize model cache"""
        try:
            cleaned = await self.cleanup_expired()
            return {"cleaned_entries": cleaned}
        except Exception as e:
            logger.error(f"Error during ModelCacheAdapter optimize: {e}", exc_info=True)
            return {"error": str(e)}

    async def start(self) -> None:
        """Start adapter"""
        self._running = True

    async def stop(self) -> None:
        """Stop adapter"""
        self._running = False

    def is_running(self) -> bool:
        """Check if adapter is running"""
        return self._running


class SmartCacheAdapter:
    """
    Adapter for SmartCache to implement unified cache interface

    Provides a thin wrapper around SmartCache to match the unified interface
    while preserving SmartCache's advanced features.
    """

    def __init__(self, smart_cache):
        self.smart_cache = smart_cache
        self._running = False

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from smart cache with unified interface"""
        return await self.smart_cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1,
    ) -> bool:
        """Set value in smart cache with unified interface"""
        return await self.smart_cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from smart cache"""
        return await self.smart_cache.delete(key)

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear smart cache"""
        await self.smart_cache.clear()
        return 0  # SmartCache.clear() doesn't return count

    async def has(self, key: str) -> bool:
        """Check if key exists in smart cache"""
        # SmartCache doesn't have a direct has() method, so we try to get
        try:
            value = await self.smart_cache.get(key)
            return value is not None
        except Exception as e:
            logger.warning(f"Error during SmartCacheAdapter has for key {key}: {e}")
            return False

    async def get_many(
        self, keys: List[str], category: str = "default"
    ) -> Dict[str, Any]:
        """Get multiple values from smart cache"""
        results = {}
        for key in keys:
            value = await self.get(key, category)
            if value is not None:
                results[key] = value
        return results

    async def set_many(
        self,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> int:
        """Set multiple values in smart cache"""
        success_count = 0
        for key, value in key_value_pairs.items():
            if await self.set(key, value, ttl, category):
                success_count += 1
        return success_count

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from smart cache"""
        success_count = 0
        for key in keys:
            if await self.delete(key):
                success_count += 1
        return success_count

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key (not directly supported by SmartCache)"""
        # SmartCache doesn't support changing TTL of existing keys
        return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key (not supported by SmartCache)"""
        return -1

    async def get_stats(self) -> Dict[str, Any]:
        """Get smart cache statistics"""
        try:
            smart_stats = self.smart_cache.get_stats()
            return {
                "type": "smart_cache_adapter",
                "smart_cache_stats": smart_stats,
            }
        except Exception as e:
            logger.error(
                f"Error during SmartCacheAdapter get_stats: {e}", exc_info=True
            )
            return {"error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get cache statistics synchronously"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.get_stats())
        finally:
            loop.close()

    async def get_categories(self) -> List[str]:
        """Get cache categories (SmartCache doesn't support categories)"""
        return ["default"]

    async def clear_category(self, category: str) -> int:
        """Clear category (not supported by SmartCache)"""
        return 0

    async def cleanup_expired(self) -> int:
        """Cleanup expired entries (handled automatically by SmartCache)"""
        return 0

    async def optimize(self) -> Dict[str, Any]:
        """Optimize smart cache (no specific optimization needed)"""
        return {"status": "no_optimization_needed"}

    async def start(self) -> None:
        """Start adapter"""
        if hasattr(self.smart_cache, "start"):
            await self.smart_cache.start()
        self._running = True

    async def stop(self) -> None:
        """Stop adapter"""
        if hasattr(self.smart_cache, "stop"):
            await self.smart_cache.stop()
        self._running = False

    def is_running(self) -> bool:
        """Check if adapter is running"""
        return self._running


class UnifiedCacheAdapter:
    """
    Adapter for UnifiedCache to implement unified cache interface

    Since UnifiedCache already implements most of the interface,
    this adapter provides a thin wrapper for consistency.
    """

    def __init__(self, unified_cache):
        self.unified_cache = unified_cache

    async def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Get value from unified cache"""
        return await self.unified_cache.get(key, category)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = "default",
        priority: int = 1,
    ) -> bool:
        """Set value in unified cache"""
        return await self.unified_cache.set(key, value, ttl, category, priority)

    async def delete(self, key: str) -> bool:
        """Delete key from unified cache"""
        return await self.unified_cache.delete(key)

    async def clear(self, category: Optional[str] = None) -> int:
        """Clear unified cache"""
        return await self.unified_cache.clear(category)

    async def has(self, key: str) -> bool:
        """Check if key exists in unified cache"""
        value = await self.unified_cache.get(key)
        return value is not None

    async def get_many(
        self, keys: List[str], category: str = "default"
    ) -> Dict[str, Any]:
        """Get multiple values from unified cache"""
        results = {}
        for key in keys:
            value = await self.get(key, category)
            if value is not None:
                results[key] = value
        return results

    async def set_many(
        self,
        key_value_pairs: Dict[str, Any],
        ttl: Optional[int] = None,
        category: str = "default",
    ) -> int:
        """Set multiple values in unified cache"""
        success_count = 0
        for key, value in key_value_pairs.items():
            if await self.set(key, value, ttl, category):
                success_count += 1
        return success_count

    async def delete_many(self, keys: List[str]) -> int:
        """Delete multiple keys from unified cache"""
        success_count = 0
        for key in keys:
            if await self.delete(key):
                success_count += 1
        return success_count

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key (not supported by UnifiedCache)"""
        return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key (not supported by UnifiedCache)"""
        return -1

    async def get_stats(self) -> Dict[str, Any]:
        """Get unified cache statistics"""
        try:
            stats = await self.unified_cache.get_stats()
            return {
                "type": "unified_cache_adapter",
                "unified_cache_stats": stats,
            }
        except Exception as e:
            logger.error(
                f"Error during UnifiedCacheAdapter get_stats: {e}", exc_info=True
            )
            return {"error": str(e)}

    def get_sync_stats(self) -> Dict[str, Any]:
        """Get cache statistics synchronously"""
        return self.unified_cache.get_stats()

    async def get_categories(self) -> List[str]:
        """Get cache categories"""
        stats = await self.unified_cache.get_stats()
        return stats.get("categories", {}).keys()

    async def clear_category(self, category: str) -> int:
        """Clear category"""
        return await self.unified_cache.clear(category)

    async def cleanup_expired(self) -> int:
        """Cleanup expired entries (handled automatically)"""
        return 0

    async def optimize(self) -> Dict[str, Any]:
        """Optimize unified cache"""
        return {"status": "optimization_handled_by_unified_cache"}

    async def start(self) -> None:
        """Start adapter"""
        await self.unified_cache.start()

    async def stop(self) -> None:
        """Stop adapter"""
        await self.unified_cache.stop()

    def is_running(self) -> bool:
        """Check if adapter is running"""
        return hasattr(self.unified_cache, "_running") and self.unified_cache._running


# Factory functions for creating adapted caches
def adapt_model_cache(model_cache) -> ICache:
    """Create adapter for ModelCache instance"""
    return ModelCacheAdapter(model_cache)


def adapt_smart_cache(smart_cache) -> ICache:
    """Create adapter for SmartCache instance"""
    return SmartCacheAdapter(smart_cache)


def adapt_unified_cache(unified_cache) -> ICache:
    """Create adapter for UnifiedCache instance"""
    return UnifiedCacheAdapter(unified_cache)


# Utility functions for migration
async def migrate_model_cache_to_unified(
    model_cache, unified_cache, category: str = "models"
) -> Dict[str, Any]:
    """Migrate data from ModelCache to UnifiedCache"""
    results = {"migrated": 0, "failed": 0, "errors": []}

    try:
        # ModelCache doesn't expose internal storage easily
        # This would need to be adapted based on ModelCache's actual structure
        # For now, return empty results as migration should be handled by CacheMigrationService
        pass
    except Exception as e:
        results["errors"].append(str(e))

    return results


async def migrate_smart_cache_to_unified(
    smart_cache, unified_cache, category: str = "responses"
) -> Dict[str, Any]:
    """Migrate data from SmartCache to UnifiedCache"""
    results = {"migrated": 0, "failed": 0, "errors": []}

    try:
        # SmartCache uses _cache OrderedDict
        if hasattr(smart_cache, "_cache"):
            for key, entry in smart_cache._cache.items():
                try:
                    success = await unified_cache.set(
                        key=key,
                        value=entry.value,
                        ttl=entry.ttl,
                        category=category,
                        priority=1,
                    )
                    if success:
                        results["migrated"] += 1
                    else:
                        results["failed"] += 1
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Failed to migrate {key}: {e}")
    except Exception as e:
        results["errors"].append(str(e))

    return results
