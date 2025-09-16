"""Model discovery caching layer with TTL support and persistence."""

import json
import logging
import os
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib

try:
    from cachetools import TTLCache

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

    # Fallback implementation
    class TTLCache:
        def __init__(self, maxsize: int, ttl: int):
            self.maxsize = maxsize
            self.ttl = ttl
            self._cache = {}
            self._timestamps = {}
            self._lock = threading.RLock()

        def __getitem__(self, key):
            with self._lock:
                if key not in self._cache:
                    raise KeyError(key)
                if datetime.now() - self._timestamps[key] > timedelta(
                    seconds=self.ttl
                ):
                    del self._cache[key]
                    del self._timestamps[key]
                    raise KeyError(key)
                return self._cache[key]

        def __setitem__(self, key, value):
            with self._lock:
                if len(self._cache) >= self.maxsize:
                    # Simple eviction - remove oldest
                    oldest_key = min(
                        self._timestamps, key=self._timestamps.get
                    )
                    del self._cache[oldest_key]
                    del self._timestamps[oldest_key]
                self._cache[key] = value
                self._timestamps[key] = datetime.now()

        def __delitem__(self, key):
            with self._lock:
                del self._cache[key]
                del self._timestamps[key]

        def __contains__(self, key):
            try:
                self[key]
                return True
            except KeyError:
                return False

        def pop(self, key, default=None):
            with self._lock:
                if key in self._cache:
                    value = self._cache.pop(key)
                    self._timestamps.pop(key)
                    return value
                return default

        def clear(self):
            with self._lock:
                self._cache.clear()
                self._timestamps.clear()

        def __len__(self):
            with self._lock:
                return len(self._cache)

        def keys(self):
            with self._lock:
                # Return a list to match cachetools behavior
                return list(self._cache.keys())

        def get(self, key, default=None):
            """Get value for key, return default if key doesn't exist."""
            try:
                return self[key]
            except KeyError:
                return default

        def items(self):
            """Return a list of (key, value) pairs."""
            with self._lock:
                return [
                    (k, self[k])
                    for k in list(self._cache.keys())
                    if k in self._cache
                ]


from .model_info import ModelInfo
from .feature_flags import get_feature_flag_manager, is_feature_enabled

logger = logging.getLogger(__name__)


class ModelCache:
    """
    Thread-safe model discovery cache with TTL support and disk persistence.

    This class provides caching for model discovery results with the following features:
    - TTL-based expiration (configurable)
    - Thread-safe operations
    - Optional disk persistence
    - Automatic cache key generation
    - Cache invalidation support

    Attributes:
        ttl: Time-to-live for cache entries in seconds
        max_size: Maximum number of cache entries
        persist: Whether to enable disk persistence
        cache_dir: Directory for cache persistence files
    """

    def __init__(
        self,
        ttl: int = 300,
        max_size: int = 1000,
        persist: bool = False,
        cache_dir: Optional[Path] = None,
    ):
        """
        Initialize the model cache.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 300)
            max_size: Maximum number of cache entries (default: 1000)
            persist: Whether to enable disk persistence (default: False)
            cache_dir: Directory for cache persistence files (default: None)
        """
        # Feature flag manager
        self._feature_manager = get_feature_flag_manager()

        # Apply feature flags
        self.persist = persist or is_feature_enabled("model_cache_persistence")

        if is_feature_enabled("model_cache_ttl_extension"):
            # Extend TTL by 50% when feature is enabled
            self.ttl = int(ttl * 1.5)
            logger.info("Model cache TTL extension enabled")
        else:
            self.ttl = ttl

        self.max_size = max_size
        self.cache_dir = cache_dir or Path.cwd() / ".cache" / "model_discovery"

        # Thread-safe cache implementation
        self._cache = TTLCache(maxsize=max_size, ttl=self.ttl)
        self._lock = threading.RLock()

        # Ensure cache directory exists
        if self.persist:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_from_disk()

        logger.info(
            f"ModelCache initialized: ttl={self.ttl}s, max_size={max_size}, "
            f"persist={self.persist}, cache_dir={self.cache_dir}"
        )

    def _generate_cache_key(self, provider_name: str, base_url: str) -> str:
        """
        Generate a unique cache key for provider models.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            MD5 hash string as cache key
        """
        key_string = f"{provider_name}:{base_url}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_disk(self) -> None:
        """Load cache entries from disk persistence."""
        if not self.persist or not self.cache_dir.exists():
            return

        try:
            with self._lock:
                for cache_file in self.cache_dir.glob("*.json"):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        cache_key = cache_file.stem
                        models_data = data.get("models", [])
                        timestamp = datetime.fromisoformat(
                            data.get("timestamp", "")
                        )

                        # Check if entry is still valid
                        if datetime.now() - timestamp < timedelta(
                            seconds=self.ttl
                        ):
                            models = [
                                ModelInfo.from_dict(m) for m in models_data
                            ]
                            self._cache[cache_key] = models
                            logger.debug(
                                f"Loaded cache entry from disk: {cache_key}"
                            )

                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.warning(
                            f"Failed to load cache file {cache_file}: {e}"
                        )
                        # Remove invalid cache file
                        cache_file.unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")

    def _save_to_disk(self, cache_key: str, models: List[ModelInfo]) -> None:
        """Save cache entry to disk persistence."""
        if not self.persist:
            return

        try:
            cache_file = self._get_cache_file_path(cache_key)
            data = {
                "models": [model.to_dict() for model in models],
                "timestamp": datetime.now().isoformat(),
                "provider": cache_key,
            }

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved cache entry to disk: {cache_key}")

        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")

    def get_models(
        self, provider_name: str, base_url: str
    ) -> Optional[List[ModelInfo]]:
        """
        Get cached models for a provider.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            List of ModelInfo objects if cached and valid, None otherwise
        """
        cache_key = self._generate_cache_key(provider_name, base_url)

        with self._lock:
            try:
                models = self._cache[cache_key]
                logger.debug(
                    f"Cache hit for {provider_name}: {len(models)} models"
                )
                return models
            except KeyError:
                logger.debug(f"Cache miss for {provider_name}")
                return None

    def set_models(
        self, provider_name: str, base_url: str, models: List[ModelInfo]
    ) -> None:
        """
        Cache models for a provider.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider
            models: List of ModelInfo objects to cache
        """
        cache_key = self._generate_cache_key(provider_name, base_url)

        with self._lock:
            self._cache[cache_key] = models
            logger.debug(f"Cached {len(models)} models for {provider_name}")

            if self.persist:
                self._save_to_disk(cache_key, models)

    def invalidate(self, provider_name: str, base_url: str) -> bool:
        """
        Invalidate cache entry for a specific provider.

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            True if entry was invalidated, False if not found
        """
        cache_key = self._generate_cache_key(provider_name, base_url)

        with self._lock:
            if cache_key in self._cache:
                try:
                    # For cachetools.TTLCache
                    if hasattr(self._cache, "pop"):
                        self._cache.pop(cache_key, None)
                    else:
                        # For fallback implementation
                        del self._cache[cache_key]
                except KeyError:
                    pass

                if self.persist:
                    cache_file = self._get_cache_file_path(cache_key)
                    cache_file.unlink(missing_ok=True)

                logger.info(f"Invalidated cache for {provider_name}")
                return True

            logger.debug(f"No cache entry to invalidate for {provider_name}")
            return False

    def invalidate_all(self) -> int:
        """
        Invalidate all cache entries.

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()

            if self.persist and self.cache_dir.exists():
                for cache_file in self.cache_dir.glob("*.json"):
                    cache_file.unlink(missing_ok=True)

            logger.info(f"Invalidated all cache entries ({count} total)")
            return count

    def is_valid(self, provider_name: str, base_url: str) -> bool:
        """
        Check if cache entry is valid (exists and not expired).

        Args:
            provider_name: Name of the provider
            base_url: Base URL of the provider

        Returns:
            True if cache entry is valid, False otherwise
        """
        cache_key = self._generate_cache_key(provider_name, base_url)

        with self._lock:
            return cache_key in self._cache

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "persist": self.persist,
                "cache_dir": str(self.cache_dir),
                "hit_ratio": 0.0,  # Could be extended with hit/miss tracking
            }

    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries.

        Returns:
            Number of entries cleaned up
        """
        # TTLCache automatically handles expiration
        # This method is for explicit cleanup if needed
        with self._lock:
            initial_size = len(self._cache)
            # Force expiration check by accessing all items
            expired_keys = []
            for key in list(self._cache.keys()):
                try:
                    _ = self._cache[key]
                except KeyError:
                    expired_keys.append(key)

            if self.persist:
                for key in expired_keys:
                    cache_file = self._get_cache_file_path(key)
                    cache_file.unlink(missing_ok=True)

            cleaned = initial_size - len(self._cache)
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} expired cache entries")

            return cleaned

    def close(self) -> None:
        """Close the cache and cleanup resources."""
        with self._lock:
            self._cache.clear()
            logger.info("ModelCache closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
