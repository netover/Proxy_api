"""Comprehensive tests for model discovery caching layer."""

import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.model_cache import ModelCache
from src.core.cache_manager import CacheManager
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.models.model_info import ModelInfo


class TestModelCache:
    """Test cases for ModelCache class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_model_cache_initialization(self):
        """Test ModelCache initialization with default parameters."""
        cache = ModelCache()

        assert cache.ttl == 300
        assert cache.max_size == 1000
        assert cache.persist is False
        assert cache.cache_dir == Path.cwd() / ".cache" / "model_discovery"

    def test_model_cache_custom_parameters(self):
        """Test ModelCache initialization with custom parameters."""
        cache = ModelCache(
            ttl=600, max_size=500, persist=True, cache_dir=self.cache_dir
        )

        assert cache.ttl == 600
        assert cache.max_size == 500
        assert cache.persist is True
        assert cache.cache_dir == self.cache_dir
        assert cache.cache_dir.exists()

    def test_cache_key_generation(self):
        """Test cache key generation consistency."""
        cache = ModelCache()

        key1 = cache._generate_cache_key("openai", "https://api.openai.com")
        key2 = cache._generate_cache_key("openai", "https://api.openai.com")
        key3 = cache._generate_cache_key("anthropic", "https://api.anthropic.com")

        assert key1 == key2
        assert key1 != key3
        assert len(key1) == 32  # MD5 hash length

    def test_set_and_get_models(self):
        """Test setting and getting models from cache."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id="gpt-4",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
        ]

        # Test cache miss
        cached = cache.get_models("openai", "https://api.openai.com")
        assert cached is None

        # Test cache set and get
        cache.set_models("openai", "https://api.openai.com", models)
        cached = cache.get_models("openai", "https://api.openai.com")

        assert cached is not None
        assert len(cached) == 2
        assert cached[0].id == "gpt-4"
        assert cached[1].id == "gpt-3.5-turbo"

    def test_cache_invalidation(self):
        """Test cache invalidation functionality."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test", "https://test.com", models)
        assert cache.is_valid("test", "https://test.com") is True

        # Invalidate specific provider
        invalidated = cache.invalidate("test", "https://test.com")
        assert invalidated is True
        assert cache.is_valid("test", "https://test.com") is False

        # Test invalidating non-existent entry
        invalidated = cache.invalidate("nonexistent", "https://test.com")
        assert invalidated is False

    def test_cache_invalidate_all(self):
        """Test invalidating all cache entries."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("provider1", "https://test1.com", models)
        cache.set_models("provider2", "https://test2.com", models)

        assert cache.invalidate_all() == 2
        assert cache.get_stats()["size"] == 0

    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        cache = ModelCache(ttl=1)  # 1 second TTL

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test", "https://test.com", models)
        assert cache.is_valid("test", "https://test.com") is True

        # Wait for expiration
        time.sleep(1.1)

        # Cache should be expired
        cached = cache.get_models("test", "https://test.com")
        assert cached is None

    def test_cache_persistence(self):
        """Test disk persistence functionality."""
        cache = ModelCache(ttl=300, persist=True, cache_dir=self.cache_dir)

        models = [
            ModelInfo(
                id="gpt-4",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
        ]

        # Set models and save to disk
        cache.set_models("openai", "https://api.openai.com", models)

        # Verify cache file exists
        cache_key = cache._generate_cache_key("openai", "https://api.openai.com")
        cache_file = cache._get_cache_file_path(cache_key)
        assert cache_file.exists()

        # Load from disk
        new_cache = ModelCache(ttl=300, persist=True, cache_dir=self.cache_dir)

        cached = new_cache.get_models("openai", "https://api.openai.com")
        assert cached is not None
        assert len(cached) == 2

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test1", "https://test1.com", models)
        cache.set_models("test2", "https://test2.com", models)

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 1000
        assert stats["ttl"] == 300
        assert stats["persist"] is False

    def test_thread_safety(self):
        """Test thread-safe operations."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id=f"model-{i}",
                object="model",
                created=1234567890,
                owned_by="test",
            )
            for i in range(100)
        ]

        def worker(thread_id):
            provider_name = f"provider-{thread_id}"
            cache.set_models(provider_name, f"https://{provider_name}.com", models)
            cached = cache.get_models(provider_name, f"https://{provider_name}.com")
            assert cached is not None
            assert len(cached) == 100

        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All operations should complete without errors
        assert cache.get_stats()["size"] == 10

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired cache entries."""
        cache = ModelCache(ttl=1)

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test", "https://test.com", models)
        assert cache.get_stats()["size"] == 1

        time.sleep(1.1)

        cleaned = cache.cleanup_expired()
        assert cleaned == 1
        assert cache.get_stats()["size"] == 0

    def test_cache_context_manager(self):
        """Test cache as context manager."""
        with ModelCache() as cache:
            models = [
                ModelInfo(
                    id="test-model",
                    object="model",
                    created=1234567890,
                    owned_by="test",
                )
            ]
            cache.set_models("test", "https://test.com", models)
            assert cache.get_stats()["size"] == 1

        # Cache should be closed after context exit


class TestCacheManager:
    """Test cases for CacheManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.fixture
    def mock_discovery_service(self):
        """Mock discovery service."""
        service = MagicMock(spec=ModelDiscoveryService)
        service.discover_models = AsyncMock()
        return service

    @pytest.fixture
    def sample_models(self):
        """Sample models for testing."""
        return [
            ModelInfo(
                id="gpt-4",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                object="model",
                created=1234567890,
                owned_by="openai",
            ),
        ]

    @pytest.mark.asyncio
    async def test_cache_manager_initialization(self, mock_discovery_service):
        """Test CacheManager initialization."""
        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=False,
        )

        assert manager.cache == cache
        assert manager.discovery_service == mock_discovery_service
        assert manager.warming_enabled is False

    @pytest.mark.asyncio
    async def test_get_models_with_cache_hit(
        self, mock_discovery_service, sample_models
    ):
        """Test getting models with cache hit."""
        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=False,
        )

        # Pre-populate cache
        provider_config = ProviderConfig(
            name="openai",
            base_url="https://api.openai.com",
            api_key="test-key",
        )

        cache.set_models("openai", "https://api.openai.com", sample_models)

        # Should return cached models without calling discovery service
        models = await manager.get_models_with_cache(provider_config)

        assert len(models) == 2
        assert models[0].id == "gpt-4"
        mock_discovery_service.discover_models.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_models_with_cache_miss(
        self, mock_discovery_service, sample_models
    ):
        """Test getting models with cache miss."""
        mock_discovery_service.discover_models.return_value = sample_models

        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=False,
        )

        provider_config = ProviderConfig(
            name="openai",
            base_url="https://api.openai.com",
            api_key="test-key",
        )

        models = await manager.get_models_with_cache(provider_config)

        assert len(models) == 2
        mock_discovery_service.discover_models.assert_called_once_with(provider_config)

        # Verify cache was populated
        cached = cache.get_models("openai", "https://api.openai.com")
        assert cached is not None
        assert len(cached) == 2

    @pytest.mark.asyncio
    async def test_get_models_force_refresh(
        self, mock_discovery_service, sample_models
    ):
        """Test force refresh bypasses cache."""
        mock_discovery_service.discover_models.return_value = sample_models

        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=False,
        )

        provider_config = ProviderConfig(
            name="openai",
            base_url="https://api.openai.com",
            api_key="test-key",
        )

        # Pre-populate cache
        cache.set_models("openai", "https://api.openai.com", [])

        # Force refresh should ignore cache
        models = await manager.get_models_with_cache(
            provider_config, force_refresh=True
        )

        assert len(models) == 2
        mock_discovery_service.discover_models.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_warming(self, mock_discovery_service, sample_models):
        """Test cache warming functionality."""
        mock_discovery_service.discover_models.return_value = sample_models

        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=True,
        )

        provider_configs = [
            ProviderConfig(
                name="openai",
                base_url="https://api.openai.com",
                api_key="test-key",
            ),
            ProviderConfig(
                name="anthropic",
                base_url="https://api.anthropic.com",
                api_key="test-key",
            ),
        ]

        results = await manager.warm_cache(provider_configs)

        assert results["status"] == "completed"
        assert len(results["providers"]) == 2
        assert results["total_models"] == 4  # 2 providers * 2 models each

        # Verify cache was populated
        for config in provider_configs:
            cached = cache.get_models(config.name, config.base_url)
            assert cached is not None
            assert len(cached) == 2

    @pytest.mark.asyncio
    async def test_cache_warming_with_errors(self, mock_discovery_service):
        """Test cache warming with some providers failing."""
        mock_discovery_service.discover_models.side_effect = [
            [
                ModelInfo(
                    id="model1",
                    object="model",
                    created=1234567890,
                    owned_by="test",
                )
            ],
            Exception("Provider unavailable"),
        ]

        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=True,
        )

        provider_configs = [
            ProviderConfig(
                name="provider1",
                base_url="https://provider1.com",
                api_key="test-key",
            ),
            ProviderConfig(
                name="provider2",
                base_url="https://provider2.com",
                api_key="test-key",
            ),
        ]

        results = await manager.warm_cache(provider_configs)

        assert results["status"] == "completed"
        assert len(results["providers"]) == 2
        assert results["total_models"] == 1
        assert len(results["errors"]) == 1
        assert results["errors"][0]["provider"] == "provider2"

    def test_cache_key_generation_consistency(self):
        """Test cache key generation consistency between cache and manager."""
        cache = ModelCache()
        manager = CacheManager(warming_enabled=False)

        key1 = cache._generate_cache_key("test", "https://test.com")
        key2 = manager.generate_cache_key("test", "https://test.com")

        assert key1 == key2

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = ModelCache()
        manager = CacheManager(cache=cache, warming_enabled=False)

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]
        cache.set_models("test", "https://test.com", models)

        stats = manager.get_cache_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 1000
        assert stats["warming_enabled"] is False
        assert stats["background_refresh_running"] is False

    def test_background_refresh_lifecycle(self):
        """Test background refresh start/stop lifecycle."""
        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            warming_enabled=False,
            refresh_interval=1,  # Short interval for testing
        )

        # Start background refresh
        manager.start_background_refresh()
        assert manager.get_cache_stats()["background_refresh_running"] is True

        # Stop background refresh
        manager.stop_background_refresh()
        assert manager.get_cache_stats()["background_refresh_running"] is False

    def test_provider_invalidation(self):
        """Test provider-specific invalidation."""
        cache = ModelCache()
        manager = CacheManager(cache=cache, warming_enabled=False)

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test", "https://test.com", models)
        assert cache.is_valid("test", "https://test.com") is True

        invalidated = manager.invalidate_provider("test", "https://test.com")
        assert invalidated is True
        assert cache.is_valid("test", "https://test.com") is False

    def test_all_invalidation(self):
        """Test invalidating all cache entries."""
        cache = ModelCache()
        manager = CacheManager(cache=cache, warming_enabled=False)

        models = [
            ModelInfo(
                id="test-model",
                object="model",
                created=1234567890,
                owned_by="test",
            )
        ]

        cache.set_models("test1", "https://test1.com", models)
        cache.set_models("test2", "https://test2.com", models)

        invalidated = manager.invalidate_all()
        assert invalidated == 2
        assert cache.get_stats()["size"] == 0

    @pytest.mark.asyncio
    async def test_close_cleanup(self, mock_discovery_service):
        """Test proper cleanup on close."""
        cache = ModelCache()
        manager = CacheManager(
            cache=cache,
            discovery_service=mock_discovery_service,
            warming_enabled=False,
        )

        # Start background refresh
        manager.start_background_refresh()

        # Close should stop background refresh
        await manager.close()

        stats = manager.get_cache_stats()
        assert stats["background_refresh_running"] is False


class TestIntegration:
    """Integration tests for caching layer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_end_to_end_caching_workflow(self):
        """Test complete caching workflow."""
        # Create real cache and discovery service
        cache = ModelCache(ttl=60, persist=True, cache_dir=self.cache_dir)

        discovery_service = ModelDiscoveryService()

        # Create cache manager
        manager = CacheManager(
            cache=cache,
            discovery_service=discovery_service,
            warming_enabled=True,
        )

        # Test provider configuration
        provider_config = ProviderConfig(
            name="test-provider",
            base_url="https://api.example.com",
            api_key="test-key",
            timeout=5,
            max_retries=1,
        )

        try:
            # Test cache warming
            results = await manager.warm_cache([provider_config])
            assert results["status"] in ["completed", "errors"]

            # Test cache retrieval
            models = await manager.get_models_with_cache(provider_config)
            assert isinstance(models, list)

            # Test cache invalidation
            invalidated = manager.invalidate_provider(
                provider_config.name, provider_config.base_url
            )
            assert isinstance(invalidated, bool)

            # Test cache stats
            stats = manager.get_cache_stats()
            assert "size" in stats
            assert "max_size" in stats

        finally:
            await manager.close()

    def test_concurrent_access_patterns(self):
        """Test concurrent access patterns."""
        cache = ModelCache()

        models = [
            ModelInfo(
                id=f"model-{i}",
                object="model",
                created=1234567890,
                owned_by="test",
            )
            for i in range(50)
        ]

        def concurrent_worker(worker_id):
            for i in range(10):
                provider_name = f"provider-{worker_id}-{i}"
                cache.set_models(provider_name, f"https://{provider_name}.com", models)
                cached = cache.get_models(provider_name, f"https://{provider_name}.com")
                assert cached is not None
                assert len(cached) == 50

        # Run concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify all entries exist
        assert cache.get_stats()["size"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
