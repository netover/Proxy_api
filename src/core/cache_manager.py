"""Centralized cache management for model discovery with warming and background refresh."""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading
from concurrent.futures import ThreadPoolExecutor
import time

from .model_cache import ModelCache
from .model_discovery import ModelDiscoveryService, ProviderConfig
from ..models.model_info import ModelInfo
from .unified_config import config_manager

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Centralized cache manager for model discovery operations.
    
    This class provides:
    - Centralized cache operations
    - Cache key generation
    - Cache warming and background refresh
    - Thread-safe operations
    - Integration with configuration
    
    Attributes:
        cache: ModelCache instance
        discovery_service: ModelDiscoveryService instance
        warming_enabled: Whether cache warming is enabled
        refresh_interval: Background refresh interval in seconds
    """
    
    def __init__(
        self,
        cache: Optional[ModelCache] = None,
        discovery_service: Optional[ModelDiscoveryService] = None,
        warming_enabled: bool = True,
        refresh_interval: int = 300
    ):
        """
        Initialize the cache manager.
        
        Args:
            cache: ModelCache instance (will create from config if None)
            discovery_service: ModelDiscoveryService instance
            warming_enabled: Whether to enable cache warming (default: True)
            refresh_interval: Background refresh interval in seconds (default: 300)
        """
        self.config = config_manager.load_config()
        
        # Initialize cache
        if cache is None:
            cache_config = self.config.settings.cache
            self.cache = ModelCache(
                ttl=cache_config.cache_ttl,
                max_size=1000,
                persist=cache_config.cache_persist,
                cache_dir=cache_config.cache_dir
            )
        else:
            self.cache = cache
        
        # Initialize discovery service
        self.discovery_service = discovery_service or ModelDiscoveryService()
        
        self.warming_enabled = warming_enabled
        self.refresh_interval = refresh_interval
        
        # Background refresh state
        self._refresh_thread: Optional[threading.Thread] = None
        self._refresh_stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Cache warming state
        self._warming_complete = False
        
        logger.info(
            f"CacheManager initialized: warming={warming_enabled}, "
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
        # Use the same logic as ModelCache for consistency
        return self.cache._generate_cache_key(provider_name, base_url)
    
    async def get_models_with_cache(
        self,
        provider_config: ProviderConfig,
        force_refresh: bool = False
    ) -> List[ModelInfo]:
        """
        Get models with caching support.
        
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
            provider_config.name,
            provider_config.base_url
        )
        
        # Check cache unless forcing refresh
        if not force_refresh:
            cached_models = self.cache.get_models(
                provider_config.name,
                provider_config.base_url
            )
            if cached_models is not None:
                logger.debug(
                    f"Cache hit for {provider_config.name}: "
                    f"{len(cached_models)} models"
                )
                return cached_models
        
        # Fetch from provider
        logger.debug(
            f"Cache miss/refresh for {provider_config.name}, "
            f"fetching from provider"
        )
        models = await self.discovery_service.discover_models(provider_config)
        
        # Cache the results
        self.cache.set_models(
            provider_config.name,
            provider_config.base_url,
            models
        )
        
        return models
    
    async def warm_cache(self, provider_configs: List[ProviderConfig]) -> Dict[str, Any]:
        """
        Warm the cache by pre-loading models for given providers.
        
        Args:
            provider_configs: List of provider configurations to warm
            
        Returns:
            Dictionary with warming results
        """
        if not self.warming_enabled:
            logger.info("Cache warming disabled")
            return {"status": "disabled", "providers": []}
        
        logger.info(f"Starting cache warming for {len(provider_configs)} providers")
        
        results = {
            "status": "completed",
            "providers": [],
            "total_models": 0,
            "errors": [],
            "duration": 0
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
                "error": None
            }
            
            if isinstance(result, Exception):
                provider_result["error"] = str(result)
                results["errors"].append({
                    "provider": config.name,
                    "error": str(result)
                })
                logger.error(
                    f"Cache warming failed for {config.name}: {result}"
                )
            else:
                provider_result["models"] = len(result)
                results["total_models"] += len(result)
                logger.info(
                    f"Cache warmed for {config.name}: {len(result)} models"
                )
            
            results["providers"].append(provider_result)
        
        duration = (datetime.now() - start_time).total_seconds()
        results["duration"] = duration
        
        self._warming_complete = True
        logger.info(
            f"Cache warming completed: {results['total_models']} models "
            f"from {len(provider_configs)} providers in {duration:.2f}s"
        )
        
        return results
    
    async def _warm_single_provider(
        self,
        provider_config: ProviderConfig
    ) -> List[ModelInfo]:
        """Warm cache for a single provider."""
        try:
            models = await self.discovery_service.discover_models(provider_config)
            self.cache.set_models(
                provider_config.name,
                provider_config.base_url,
                models
            )
            return models
        except Exception as e:
            logger.error(
                f"Failed to warm cache for {provider_config.name}: {e}"
            )
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
            daemon=True
        )
        self._refresh_thread.start()
        logger.info(
            f"Started background cache refresh every {self.refresh_interval}s"
        )
    
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
                        
                        refreshed = sum(1 for r in results if not isinstance(r, Exception))
                        errors = sum(1 for r in results if isinstance(r, Exception))
                        
                        logger.info(
                            f"Background refresh completed: "
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
                max_retries=provider_config.max_retries
            )
            
            await self.get_models_with_cache(
                discovery_config,
                force_refresh=True
            )
            
        except Exception as e:
            logger.error(
                f"Background refresh failed for {provider_config.name}: {e}"
            )
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
        return self.cache.invalidate(provider_name, base_url)
    
    def invalidate_all(self) -> int:
        """
        Invalidate all cache entries.
        
        Returns:
            Number of entries invalidated
        """
        return self.cache.invalidate_all()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = self.cache.get_stats()
        stats.update({
            'warming_enabled': self.warming_enabled,
            'refresh_interval': self.refresh_interval,
            'background_refresh_running': (
                self._refresh_thread is not None and
                self._refresh_thread.is_alive()
            ),
            'warming_complete': self._warming_complete
        })
        return stats
    
    def is_warming_complete(self) -> bool:
        """Check if cache warming is complete."""
        return self._warming_complete
    
    async def close(self) -> None:
        """Close the cache manager and cleanup resources."""
        self.stop_background_refresh()
        self._executor.shutdown(wait=True)
        await self.discovery_service.close()
        self.cache.close()
        logger.info("CacheManager closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # Note: async close needs to be called explicitly
        pass


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.
    
    Returns:
        CacheManager instance
    """
    global _cache_manager
    
    if _cache_manager is None:
        _cache_manager = CacheManager()
    
    return _cache_manager


def reset_cache_manager() -> None:
    """Reset the global cache manager instance."""
    global _cache_manager
    
    if _cache_manager is not None:
        # Note: async close needs to be handled by caller
        _cache_manager = None