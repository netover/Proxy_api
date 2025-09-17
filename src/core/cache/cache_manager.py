"""Centralized cache management for model discovery with warming and background refresh.

UNIFIED CACHE INTEGRATION:
This module has been updated to use the new UnifiedCache system while maintaining
backward compatibility with existing code during the transition period.
"""

import asyncio
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.model_info import ModelInfo
from .cache_monitor import CacheMonitor
from .cache_warmer import CacheWarmer, record_cache_access

# Legacy imports for backward compatibility
from .model_cache import ModelCache
from .model_discovery import ModelDiscoveryService, ProviderConfig

# Unified cache system imports
from .unified_cache import UnifiedCache
from .unified_config import config_manager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache manager for model discovery operations with unified cache integration.

    This class provides:
    - Centralized cache operations with unified cache system
    - Cache key generation with unified cache compatibility
    - Intelligent cache warming and background refresh
    - Thread-safe operations
    - Integration with configuration
    - Backward compatibility with existing code

    Attributes:
        unified_cache: UnifiedCache instance (primary cache)
        legacy_cache: ModelCache instance (for backward compatibility)
        cache_warmer: CacheWarmer instance (for intelligent warming)
        cache_monitor: CacheMonitor instance (for monitoring and alerts)
        discovery_service: ModelDiscoveryService instance
        use_unified_cache: Whether to use unified cache (default: True)
    """

    def __init__(
        self,
        cache: Optional[UnifiedCache] = None,
        discovery_service: Optional[ModelDiscoveryService] = None,
        warming_enabled: bool = True,
        refresh_interval: int = 300,
        use_unified_cache: bool = True,  # New parameter for unified cache
        enable_monitoring: bool = True,
    ):
        """
        Initialize the cache manager with unified cache support.

        Args:
            cache: UnifiedCache instance (will create from config if None)
            discovery_service: ModelDiscoveryService instance
            warming_enabled: Whether to enable cache warming (default: True)
            refresh_interval: Background refresh interval in seconds (default: 300)
            use_unified_cache: Whether to use unified cache system (default: True)
            enable_monitoring: Whether to enable cache monitoring (default: True)
        """
        # Load config only if we need it for provider configurations
        # If cache is provided, we can skip full config loading
        if cache is None:
            self.config = config_manager.load_config()
        else:
            # Create minimal config for cache settings
            try:
                self.config = config_manager.load_config()
            except (
                FileNotFoundError,
                OSError,
                json.JSONDecodeError,
                ImportError,
            ) as e:
                # If config loading fails due to file issues, JSON parsing, or import errors, create minimal config
                logger.warning(f"Config loading failed, using minimal config: {e}")
                from types import SimpleNamespace

                self.config = SimpleNamespace()
                self.config.settings = SimpleNamespace()
                self.config.settings.cache = SimpleNamespace()
                self.config.settings.cache.cache_enabled = True
                self.config.settings.cache.cache_ttl = 1800
                self.config.settings.cache.max_memory_mb = 512
                self.config.settings.cache.cache_persist = True
                self.config.providers = []
        self.use_unified_cache = use_unified_cache
        self.enable_monitoring = enable_monitoring

        # Initialize unified cache (primary)
        if self.use_unified_cache:
            if cache is None:
                cache_config = getattr(self.config.settings, "cache", None)
                if cache_config:
                    self.unified_cache = UnifiedCache(
                        max_size=getattr(cache_config, "max_size", 10000),
                        default_ttl=getattr(cache_config, "cache_ttl", 1800),
                        max_memory_mb=getattr(cache_config, "max_memory_mb", 512),
                        enable_disk_cache=getattr(cache_config, "cache_persist", True),
                        cache_dir=getattr(cache_config, "cache_dir", None),
                        enable_smart_ttl=True,
                        enable_predictive_warming=warming_enabled,
                        enable_consistency_monitoring=enable_monitoring,
                    )
                else:
                    self.unified_cache = UnifiedCache()
            else:
                self.unified_cache = cache

            # Set cache reference for backward compatibility
            self.cache = self.unified_cache
        else:
            # Fallback to legacy ModelCache
            cache_config = self.config.settings.cache
            self.legacy_cache = ModelCache(
                ttl=cache_config.cache_ttl,
                max_size=1000,
                persist=cache_config.cache_persist,
                cache_dir=cache_config.cache_dir,
            )
            self.cache = self.legacy_cache
            self.unified_cache = None

        # Initialize discovery service
        self.discovery_service = discovery_service or ModelDiscoveryService()

        self.warming_enabled = warming_enabled
        self.refresh_interval = refresh_interval

        # Initialize cache warmer (unified cache only)
        if self.use_unified_cache and warming_enabled:
            self.cache_warmer = CacheWarmer(
                cache=self.unified_cache,
                enable_pattern_analysis=True,
                enable_predictive_warming=True,
            )
        else:
            self.cache_warmer = None

        # Initialize cache monitor (unified cache only)
        if self.use_unified_cache and enable_monitoring:
            from .cache_monitor import MonitorConfig

            self.cache_monitor = CacheMonitor(
                cache=self.unified_cache,
                config=MonitorConfig(
                    enable_auto_repair=True, enable_predictive_alerts=True
                ),
            )
        else:
            self.cache_monitor = None

        # Background refresh state
        self._refresh_thread: Optional[threading.Thread] = None
        self._refresh_stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Cache warming state
        self._warming_complete = False

        logger.info(
            f"CacheManager initialized: unified_cache={use_unified_cache}, "
            f"warming={warming_enabled}, monitoring={enable_monitoring}, "
            f"refresh_interval={refresh_interval}s"
        )

    def generate_cache_key(self, provider_name: str, base_url: str) -> str:
        """
        Generate a standardized cache key for provider models.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            Standardized cache key string
        """
        if self.use_unified_cache:
            # Use UnifiedCache key generation
            return self.unified_cache._generate_key(provider_name, base_url)
        else:
            # Use legacy ModelCache key generation for backward compatibility
            return self.legacy_cache._generate_cache_key(provider_name, base_url)

    async def get_models_with_cache(
        self, provider_config: ProviderConfig, force_refresh: bool = False
    ) -> List[ModelInfo]:
        """
        Get models with caching support using unified cache system.

        Args:
            provider_config: Provider configuration
            force_refresh: Whether to skip cache and force refresh

        Returns:
            List of ModelInfo objects
        """
        if not self.config.settings.cache.cache_enabled:
            # Cache disabled, fetch directly
            logger.debug("Cache disabled, fetching models directly")
            return await self.discovery_service.discover_models(provider_config)

        cache_key = self.generate_cache_key(
            provider_config.name, provider_config.base_url
        )

        # Record access for pattern analysis (unified cache only)
        if self.use_unified_cache and self.cache_warmer:
            record_cache_access(cache_key, "model_discovery")

        # Check cache unless forcing refresh
        if not force_refresh:
            if self.use_unified_cache:
                # Use UnifiedCache async API
                cached_models = await self.unified_cache.get(
                    cache_key, category="model_discovery"
                )
                if cached_models is not None:
                    logger.debug(
                        f"Cache hit for {provider_config.name}: "
                        f"{len(cached_models)} models"
                    )
                    return cached_models
            else:
                # Use legacy ModelCache API
                cached_models = self.legacy_cache.get_models(
                    provider_config.name, provider_config.base_url
                )
                if cached_models is not None:
                    logger.debug(
                        f"Cache hit for {provider_config.name}: "
                        f"{len(cached_models)} models"
                    )
                    return cached_models

        # Fetch from provider
        logger.debug(
            f"Cache miss/refresh for {provider_config.name}, " "fetching from provider"
        )
        models = await self.discovery_service.discover_models(provider_config)

        # Cache the results
        if self.use_unified_cache:
            # Use UnifiedCache async API
            success = await self.unified_cache.set(
                key=cache_key, value=models, category="model_discovery"
            )
            if not success:
                logger.warning(f"Failed to cache models for {provider_config.name}")
        else:
            # Use legacy ModelCache API
            self.legacy_cache.set_models(
                provider_config.name, provider_config.base_url, models
            )

        return models

    async def warm_cache(
        self, provider_configs: List[ProviderConfig]
    ) -> Dict[str, Any]:
        """
        Warm the cache by pre-loading models for given providers using unified warmer.

        Args:
            provider_configs: List of provider configurations to warm

        Returns:
            Dictionary with warming results
        """
        if not self.warming_enabled:
            logger.info("Cache warming disabled")
            return {"status": "disabled", "providers": []}

        if self.use_unified_cache and self.cache_warmer:
            # Use unified cache warmer for intelligent warming
            return await self._warm_with_unified_warmer(provider_configs)
        else:
            # Fallback to legacy warming
            return await self._warm_with_legacy_warmer(provider_configs)

    async def _warm_with_unified_warmer(
        self, provider_configs: List[ProviderConfig]
    ) -> Dict[str, Any]:
        """Warm cache using unified cache warmer with intelligent features."""
        logger.info(
            f"Starting intelligent cache warming for {len(provider_configs)} providers"
        )

        warming_tasks = []

        for config in provider_configs:
            # Queue warming task with the unified warmer
            success = await self.cache_warmer.warm_provider_models(
                config, priority=2  # Medium priority for batch warming
            )
            if success:
                warming_tasks.append(config)

        # Wait for warming to complete (simplified - in production this would be more sophisticated)
        await asyncio.sleep(1)

        # Get warming statistics
        stats = await self.cache_warmer.get_warming_stats()

        results = {
            "status": "completed",
            "providers": [
                {"name": config.name, "base_url": config.base_url}
                for config in warming_tasks
            ],
            "total_models": stats["total_keys_warmed"],
            "successful_warmings": stats["successful_warmings"],
            "failed_warmings": stats["failed_warmings"],
            "errors": [],
            "warming_stats": stats,
            "duration": 0,  # Would need to track actual duration
        }

        self._warming_complete = True
        logger.info(
            f"Intelligent cache warming completed: {stats['successful_warmings']} "
            f"successful, {stats['failed_warmings']} failed"
        )

        return results

    async def _warm_with_legacy_warmer(
        self, provider_configs: List[ProviderConfig]
    ) -> Dict[str, Any]:
        """Warm cache using legacy warming approach for backward compatibility."""
        logger.info(
            f"Starting legacy cache warming for {len(provider_configs)} providers"
        )

        results = {
            "status": "completed",
            "providers": [],
            "total_models": 0,
            "errors": [],
            "duration": 0,
        }

        start_time = datetime.now()

        # Process providers concurrently
        tasks = []
        for config in provider_configs:
            task = self._warm_single_provider(config)
            tasks.append(task)

        # Execute all warming tasks
        provider_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for config, result in zip(provider_configs, provider_results):
            provider_result = {
                "name": config.name,
                "base_url": config.base_url,
                "models": 0,
                "error": None,
            }

            if isinstance(result, Exception):
                provider_result["error"] = str(result)
                results["errors"].append(
                    {"provider": config.name, "error": str(result)}
                )
                logger.error(f"Cache warming failed for {config.name}: {result}")
            else:
                provider_result["models"] = len(result)
                results["total_models"] += len(result)
                logger.info(f"Cache warmed for {config.name}: {len(result)} models")

            results["providers"].append(provider_result)

        duration = (datetime.now() - start_time).total_seconds()
        results["duration"] = duration

        self._warming_complete = True
        logger.info(
            f"Legacy cache warming completed: {results['total_models']} models "
            f"from {len(provider_configs)} providers in {duration:.2f}s"
        )

        return results

    async def _warm_single_provider(
        self, provider_config: ProviderConfig
    ) -> List[ModelInfo]:
        """Warm cache for a single provider (legacy method)."""
        try:
            models = await self.discovery_service.discover_models(provider_config)

            if self.use_unified_cache:
                # Use unified cache API
                cache_key = self.generate_cache_key(
                    provider_config.name, provider_config.base_url
                )
                success = await self.unified_cache.set(
                    key=cache_key, value=models, category="model_discovery"
                )
                if not success:
                    logger.warning(f"Failed to cache models for {provider_config.name}")
            else:
                # Use legacy cache API
                self.legacy_cache.set_models(
                    provider_config.name, provider_config.base_url, models
                )

            return models
        except Exception as e:
            logger.error(f"Failed to warm cache for {provider_config.name}: {e}")
            raise

    def start_background_refresh(self) -> None:
        """Start background cache refresh thread."""
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            logger.warning("Background refresh already running")
            return

        if not self.config.settings.cache.cache_enabled:
            logger.info("Cache disabled, skipping background refresh")
            return

        self._refresh_stop_event.clear()
        self._refresh_thread = threading.Thread(
            target=self._background_refresh_worker,
            name="CacheRefreshThread",
            daemon=True,
        )
        self._refresh_thread.start()
        logger.info(f"Started background cache refresh every {self.refresh_interval}s")

    def stop_background_refresh(self) -> None:
        """Stop background cache refresh thread."""
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            logger.debug("Background refresh not running")
            return

        self._refresh_stop_event.set()
        self._refresh_thread.join(timeout=5)
        logger.info("Stopped background cache refresh")

    def _background_refresh_worker(self) -> None:
        """Background worker for cache refresh."""
        logger.info("Background cache refresh worker started")

        while not self._refresh_stop_event.wait(self.refresh_interval):
            try:
                # Get current provider configurations
                config = config_manager.load_config()
                providers = config.providers

                if not providers:
                    logger.debug("No providers configured for refresh")
                    continue

                logger.info(
                    f"Starting background refresh for {len(providers)} providers"
                )

                # Create async event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # Refresh cache for all providers
                    tasks = [
                        self._refresh_single_provider(provider)
                        for provider in providers
                        if provider.enabled
                    ]

                    if tasks:
                        results = loop.run_until_complete(
                            asyncio.gather(*tasks, return_exceptions=True)
                        )

                        refreshed = sum(
                            1 for r in results if not isinstance(r, Exception)
                        )
                        errors = sum(1 for r in results if isinstance(r, Exception))

                        logger.info(
                            "Background refresh completed: "
                            f"{refreshed} refreshed, {errors} errors"
                        )

                finally:
                    loop.close()

            except Exception as e:
                logger.error(f"Error in background refresh worker: {e}")

        logger.info("Background cache refresh worker stopped")

    async def _refresh_single_provider(self, provider_config) -> None:
        """Refresh cache for a single provider."""
        try:
            # Convert unified config provider to discovery provider config
            discovery_config = ProviderConfig(
                name=provider_config.name,
                base_url=str(provider_config.base_url),
                api_key=os.getenv(f"PROXY_API_{provider_config.api_key_env}", ""),
                timeout=provider_config.timeout,
                max_retries=provider_config.max_retries,
            )

            await self.get_models_with_cache(discovery_config, force_refresh=True)

        except Exception as e:
            logger.error(f"Background refresh failed for {provider_config.name}: {e}")
            raise

    def invalidate_provider(self, provider_name: str, base_url: str) -> bool:
        """
        Invalidate cache for a specific provider.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            True if invalidated, False if not found
        """
        if self.use_unified_cache:
            # Use unified cache invalidation
            cache_key = self.generate_cache_key(provider_name, base_url)
            return asyncio.run(self.unified_cache.delete(cache_key))
        else:
            # Use legacy cache invalidation
            return self.legacy_cache.invalidate(provider_name, base_url)

    def invalidate_all(self) -> int:
        """
        Invalidate all cache entries.

        Returns:
            Number of entries invalidated
        """
        if self.use_unified_cache:
            # Use unified cache clear (async)
            async def clear_async():
                return await self.unified_cache.clear()

            return asyncio.run(clear_async())
        else:
            # Use legacy cache invalidation
            return self.legacy_cache.invalidate_all()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics including unified components.

        Returns:
            Dictionary with cache statistics
        """
        if self.use_unified_cache:
            # Get unified cache stats (handle async properly)
            try:
                # Try to get current event loop
                asyncio.get_running_loop()
                # If we're in an async context, we need to handle this differently
                # For now, return basic stats
                stats = {
                    "entries": len(self.unified_cache._memory_cache),
                    "max_size": self.unified_cache.max_size,
                    "hit_rate": 0.0,
                    "use_unified_cache": True,
                }
            except RuntimeError:
                # No running loop, we can use asyncio.run
                stats = asyncio.run(self.unified_cache.get_stats())

            # Add warmer stats if available
            if self.cache_warmer:
                try:
                    asyncio.get_running_loop()
                    # In async context, skip detailed stats for now
                    stats["warming_stats"] = {"available": True}
                except RuntimeError:
                    warmer_stats = asyncio.run(self.cache_warmer.get_warming_stats())
                    stats["warming_stats"] = warmer_stats

            # Add monitor stats if available
            if self.cache_monitor:
                try:
                    asyncio.get_running_loop()
                    # In async context, skip detailed stats for now
                    stats["monitor_stats"] = {"available": True}
                except RuntimeError:
                    monitor_report = asyncio.run(
                        self.cache_monitor.get_monitoring_report()
                    )
                    stats["monitor_stats"] = {
                        "health": monitor_report.get("summary_stats", {}),
                        "active_alerts": len(monitor_report.get("active_alerts", [])),
                        "consistency_issues": len(
                            monitor_report.get("consistency_issues", [])
                        ),
                    }
        else:
            # Get legacy cache stats
            stats = self.legacy_cache.get_stats()

        # Add common manager stats
        stats.update(
            {
                "warming_enabled": self.warming_enabled,
                "refresh_interval": self.refresh_interval,
                "background_refresh_running": (
                    self._refresh_thread is not None and self._refresh_thread.is_alive()
                ),
                "warming_complete": self._warming_complete,
                "use_unified_cache": self.use_unified_cache,
                "monitoring_enabled": self.enable_monitoring,
            }
        )

        return stats

    def is_warming_complete(self) -> bool:
        """Check if cache warming is complete."""
        return self._warming_complete

    # Unified Cache Specific Methods

    async def get_cache_health(self) -> Dict[str, Any]:
        """Get cache health status from monitor (unified cache only)."""
        if not self.use_unified_cache or not self.cache_monitor:
            return {
                "status": "not_available",
                "message": "Unified cache monitoring not enabled",
            }

        return await self.cache_monitor.get_health_status()

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Get detailed monitoring report (unified cache only)."""
        if not self.use_unified_cache or not self.cache_monitor:
            return {"error": "Unified cache monitoring not enabled"}

        return await self.cache_monitor.get_monitoring_report()

    async def optimize_cache_performance(self) -> Dict[str, Any]:
        """Optimize cache performance using warmer insights."""
        if not self.use_unified_cache or not self.cache_warmer:
            return {"error": "Unified cache optimization not available"}

        return await self.cache_warmer.optimize_warming_strategy()

    def get_unified_cache_info(self) -> Dict[str, Any]:
        """Get information about unified cache components."""
        return {
            "use_unified_cache": self.use_unified_cache,
            "components": {
                "cache_warmer": self.cache_warmer is not None,
                "cache_monitor": self.cache_monitor is not None,
                "unified_cache": self.unified_cache is not None,
                "legacy_cache": hasattr(self, "legacy_cache")
                and self.legacy_cache is not None,
            },
            "features": {
                "smart_ttl": self.use_unified_cache
                and self.unified_cache.enable_smart_ttl,
                "predictive_warming": self.use_unified_cache
                and self.unified_cache.enable_predictive_warming,
                "consistency_monitoring": self.use_unified_cache
                and self.unified_cache.enable_consistency_monitoring,
            },
        }

    async def close(self) -> None:
        """Close the cache manager and cleanup all unified components."""
        self.stop_background_refresh()
        self._executor.shutdown(wait=True)

        # Close discovery service
        await self.discovery_service.close()

        # Close unified components
        if self.use_unified_cache:
            if self.cache_warmer:
                await self.cache_warmer.stop()
            if self.cache_monitor:
                await self.cache_monitor.stop()
            if self.unified_cache:
                await self.unified_cache.stop()

        # Close legacy cache
        if hasattr(self, "legacy_cache") and self.legacy_cache:
            self.legacy_cache.close()

        logger.info("CacheManager closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Note: async close needs to be called explicitly


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(use_unified_cache: bool = True) -> CacheManager:
    """
    Get the global cache manager instance with unified cache support.

    Args:
        use_unified_cache: Whether to use unified cache system (default: True)

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(
            use_unified_cache=use_unified_cache,
            enable_monitoring=True,  # Enable monitoring by default for unified cache
        )

    return _cache_manager


def reset_cache_manager() -> None:
    """Reset the global cache manager instance."""
    global _cache_manager

    if _cache_manager is not None:
        # Note: async close needs to be handled by caller
        _cache_manager = None
