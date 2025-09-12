"""
Backward Compatibility Layer for Cache Systems

This module provides backward compatibility for the legacy cache interfaces
during the transition to the unified cache system. It allows existing code
to continue working while gradually migrating to the new interfaces.

Features:
- Legacy ModelCache interface compatibility
- Legacy SmartCache interface compatibility
- Legacy CacheManager interface compatibility
- Automatic delegation to consolidated cache
- Deprecation warnings for old interfaces
"""

import warnings
from typing import Dict, Any, List, Optional, Union
from .consolidated_cache import get_consolidated_cache_manager_sync
from .logging import ContextualLogger

logger = ContextualLogger(__name__)


class LegacyModelCache:
    """
    Backward compatibility wrapper for ModelCache interface

    This class provides the same interface as the old ModelCache
    but delegates operations to the new ConsolidatedCacheManager.
    """

    def __init__(self, ttl: int = 300, max_size: int = 1000, persist: bool = False, cache_dir: Optional[str] = None):
        warnings.warn(
            "ModelCache is deprecated. Use ConsolidatedCacheManager instead.",
            DeprecationWarning,
            stacklevel=2
        )

        logger.info("LegacyModelCache initialized - delegating to ConsolidatedCacheManager")

        # Get the consolidated cache manager
        self._cache_manager = get_consolidated_cache_manager_sync()

        # Store legacy parameters for compatibility
        self.ttl = ttl
        self.max_size = max_size
        self.persist = persist
        self.cache_dir = cache_dir

    def _make_cache_key(self, provider_name: str, base_url: str) -> str:
        """Generate cache key for provider models"""
        return f"models:{provider_name}:{base_url}"

    def get_models(self, provider_name: str, base_url: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached models (legacy interface)"""
        key = self._make_cache_key(provider_name, base_url)
        return self._cache_manager.get(key, category="models")

    def set_models(self, provider_name: str, base_url: str, models: List[Dict[str, Any]]) -> None:
        """Cache models (legacy interface)"""
        key = self._make_cache_key(provider_name, base_url)
        self._cache_manager.set(key, models, ttl=self.ttl, category="models")

    def invalidate(self, provider_name: str, base_url: str) -> bool:
        """Invalidate cached models (legacy interface)"""
        key = self._make_cache_key(provider_name, base_url)
        return self._cache_manager.delete(key)

    def invalidate_all(self) -> int:
        """Invalidate all cached models (legacy interface)"""
        return self._cache_manager.clear(category="models")

    def is_valid(self, provider_name: str, base_url: str) -> bool:
        """Check if cached models are valid (legacy interface)"""
        key = self._make_cache_key(provider_name, base_url)
        result = self._cache_manager.get(key, category="models")
        return result is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics (legacy interface)"""
        stats = self._cache_manager.get_stats()

        # Return legacy-compatible stats format
        return {
            'size': stats.get('entries', 0),
            'max_size': self.max_size,
            'ttl': self.ttl,
            'persist': self.persist,
            'cache_dir': str(self.cache_dir) if self.cache_dir else None,
            'hit_ratio': stats.get('hit_rate', 0.0)
        }

    def cleanup_expired(self) -> int:
        """Cleanup expired entries (legacy interface)"""
        return self._cache_manager.cleanup_expired()

    def close(self) -> None:
        """Close cache (legacy interface)"""
        # Note: We don't actually close the consolidated cache manager
        # as it may be used by other components
        pass

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


class LegacySmartCache:
    """
    Backward compatibility wrapper for SmartCache interface

    This class provides the same interface as the old SmartCache
    but delegates operations to the new ConsolidatedCacheManager.
    """

    def __init__(
        self,
        max_size: int = 10000,
        default_ttl: int = 3600,
        max_memory_mb: int = 512,
        cleanup_interval: int = 300,
        enable_compression: bool = True
    ):
        warnings.warn(
            "SmartCache is deprecated. Use ConsolidatedCacheManager instead.",
            DeprecationWarning,
            stacklevel=2
        )

        logger.info("LegacySmartCache initialized - delegating to ConsolidatedCacheManager")

        # Get the consolidated cache manager
        self._cache_manager = get_consolidated_cache_manager_sync()

        # Store legacy parameters for compatibility
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cleanup_interval = cleanup_interval
        self.enable_compression = enable_compression

        # Initialize stats (legacy format)
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (legacy async interface)"""
        self.total_requests += 1
        result = await self._cache_manager.get(key, category="responses")

        if result is not None:
            self.hits += 1
        else:
            self.misses += 1

        return result

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache (legacy async interface)"""
        if ttl is None:
            ttl = self.default_ttl
        return await self._cache_manager.set(key, value, ttl=ttl, category="responses")

    async def delete(self, key: str) -> bool:
        """Delete key from cache (legacy async interface)"""
        return await self._cache_manager.delete(key)

    async def clear(self) -> None:
        """Clear cache (legacy async interface)"""
        await self._cache_manager.clear(category="responses")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics (legacy format)"""
        stats = self._cache_manager.get_stats()

        # Return legacy-compatible stats format
        return {
            'entries': stats.get('entries', 0),
            'max_size': self.max_size,
            'memory_usage_bytes': stats.get('memory_usage_bytes', 0),
            'memory_usage_mb': stats.get('memory_usage_mb', 0),
            'max_memory_mb': self.max_memory_bytes / (1024 * 1024),
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': self.total_requests,
            'hit_rate': self.hits / self.total_requests if self.total_requests > 0 else 0,
            'evictions': stats.get('evictions', 0),
            'default_ttl': self.default_ttl
        }

    async def start(self) -> None:
        """Start cache (legacy async interface)"""
        # Already started by consolidated cache manager
        pass

    async def stop(self) -> None:
        """Stop cache (legacy async interface)"""
        # Don't actually stop the consolidated cache manager
        pass

    async def get_or_set(self, key: str, getter_func, ttl: Optional[int] = None) -> Any:
        """Get or set value (legacy async interface)"""
        if ttl is None:
            ttl = self.default_ttl
        return await self._cache_manager.get_or_set(key, getter_func, ttl, "responses")


class LegacyCacheManager:
    """
    Backward compatibility wrapper for CacheManager interface

    This class provides the same interface as the old CacheManager
    but delegates operations to the new ConsolidatedCacheManager.
    """

    def __init__(
        self,
        cache=None,
        discovery_service=None,
        warming_enabled: bool = True,
        refresh_interval: int = 300,
        use_unified_cache: bool = True
    ):
        warnings.warn(
            "CacheManager is deprecated. Use ConsolidatedCacheManager instead.",
            DeprecationWarning,
            stacklevel=2
        )

        logger.info("LegacyCacheManager initialized - delegating to ConsolidatedCacheManager")

        # Get the consolidated cache manager
        self._cache_manager = get_consolidated_cache_manager_sync()

        # Store legacy parameters for compatibility
        self.warming_enabled = warming_enabled
        self.refresh_interval = refresh_interval
        self.use_unified_cache = use_unified_cache

        # Legacy attributes
        self.config = type('Config', (), {})()  # Mock config object
        self.config.settings = type('Settings', (), {})()
        self.config.settings.cache = type('Cache', (), {})()
        self.config.settings.cache.cache_enabled = True
        self.config.settings.cache.cache_ttl = 1800
        self.config.settings.cache.max_memory_mb = 512
        self.config.settings.cache.cache_persist = True

        # Mock discovery service if needed
        self.discovery_service = discovery_service

        # State variables for compatibility
        self._refresh_thread = None
        self._warming_complete = True

    def generate_cache_key(self, provider_name: str, base_url: str) -> str:
        """Generate cache key (legacy interface)"""
        return f"models:{provider_name}:{base_url}"

    async def get_models_with_cache(
        self,
        provider_config,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """Get models with caching (legacy async interface)"""
        key = self.generate_cache_key(provider_config.name, provider_config.base_url)

        if not force_refresh:
            cached = await self._cache_manager.get(key, category="models")
            if cached is not None:
                return cached

        # Fetch from provider (would need discovery service)
        if hasattr(self, 'discovery_service') and self.discovery_service:
            models = await self.discovery_service.discover_models(provider_config)

            # Cache the results
            await self._cache_manager.set(key, models, category="models")
            return models
        else:
            # Return empty list if no discovery service
            return []

    def start_background_refresh(self) -> None:
        """Start background refresh (legacy interface)"""
        # Not implemented in legacy compatibility mode
        pass

    def stop_background_refresh(self) -> None:
        """Stop background refresh (legacy interface)"""
        # Not implemented in legacy compatibility mode
        pass

    def invalidate_provider(self, provider_name: str, base_url: str) -> bool:
        """Invalidate provider cache (legacy interface)"""
        key = self.generate_cache_key(provider_name, base_url)
        return self._cache_manager.delete(key)

    def invalidate_all(self) -> int:
        """Invalidate all cache (legacy interface)"""
        return self._cache_manager.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (legacy interface)"""
        stats = self._cache_manager.get_stats()

        # Return legacy-compatible format
        return {
            'entries': stats.get('entries', 0),
            'max_size': 10000,
            'hit_rate': stats.get('hit_rate', 0.0),
            'use_unified_cache': True,
            'warming_enabled': self.warming_enabled,
            'refresh_interval': self.refresh_interval,
            'background_refresh_running': False,
            'warming_complete': self._warming_complete
        }

    def is_warming_complete(self) -> bool:
        """Check if warming is complete (legacy interface)"""
        return self._warming_complete

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health (legacy interface)"""
        return await self._cache_manager.get_cache_health()

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Get monitoring report (legacy interface)"""
        return await self._cache_manager.get_monitoring_report()


# Global functions for backward compatibility

def get_model_cache(**kwargs) -> LegacyModelCache:
    """Get legacy ModelCache instance (deprecated)"""
    return LegacyModelCache(**kwargs)


def get_smart_cache(**kwargs) -> LegacySmartCache:
    """Get legacy SmartCache instance (deprecated)"""
    return LegacySmartCache(**kwargs)


def get_cache_manager(**kwargs) -> LegacyCacheManager:
    """Get legacy CacheManager instance (deprecated)"""
    return LegacyCacheManager(**kwargs)


# Legacy global instances (deprecated)

# Note: These are provided for backward compatibility but will show deprecation warnings
# when first accessed

_model_cache_instance = None
_smart_cache_instance = None
_cache_manager_instance = None


def get_legacy_model_cache() -> LegacyModelCache:
    """Get legacy global ModelCache instance (deprecated)"""
    global _model_cache_instance
    if _model_cache_instance is None:
        _model_cache_instance = LegacyModelCache()
    return _model_cache_instance


def get_legacy_smart_cache() -> LegacySmartCache:
    """Get legacy global SmartCache instance (deprecated)"""
    global _smart_cache_instance
    if _smart_cache_instance is None:
        _smart_cache_instance = LegacySmartCache()
    return _smart_cache_instance


def get_legacy_cache_manager() -> LegacyCacheManager:
    """Get legacy global CacheManager instance (deprecated)"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = LegacyCacheManager()
    return _cache_manager_instance


# Monkey patch the old modules to use compatibility layer
def enable_backward_compatibility():
    """
    Enable backward compatibility by monkey-patching old modules

    This function can be called to enable seamless backward compatibility
    for existing code that imports from the old cache modules.
    """
    try:
        # Patch ModelCache
        import src.core.model_cache as model_cache_module
        model_cache_module.ModelCache = LegacyModelCache
        model_cache_module.get_model_cache = get_model_cache

        # Patch SmartCache
        import src.core.smart_cache as smart_cache_module
        smart_cache_module.SmartCache = LegacySmartCache
        smart_cache_module.get_response_cache = lambda: get_legacy_smart_cache()
        smart_cache_module.get_summary_cache = lambda: get_legacy_smart_cache()
        smart_cache_module.initialize_caches = lambda: None  # No-op
        smart_cache_module.shutdown_caches = lambda: None  # No-op

        # Patch CacheManager
        import src.core.cache_manager as cache_manager_module
        cache_manager_module.CacheManager = LegacyCacheManager
        cache_manager_module.get_cache_manager = get_cache_manager

        logger.info("Backward compatibility enabled - old interfaces now delegate to consolidated cache")

    except ImportError as e:
        logger.warning(f"Could not enable backward compatibility: {e}")


if __name__ == "__main__":
    # Enable backward compatibility when run directly
    enable_backward_compatibility()
    print("Backward compatibility layer enabled")
    print("Old cache interfaces will now delegate to ConsolidatedCacheManager")
    print("Deprecation warnings will be shown for old interfaces")