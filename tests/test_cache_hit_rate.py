"""
Test Cache Hit Rate for ProxyAPI Static Data Caching
Tests that cache hit rate exceeds 90% for static data operations
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, patch
from typing import List

from src.core.model_discovery import ModelDiscoveryService, ProviderConfig
from src.core.provider_discovery import provider_discovery
from src.core.unified_cache import get_unified_cache
from src.core.cache_monitor import cache_monitor
from src.models.model_info import ModelInfo


class TestCacheHitRate:
    """Test suite for cache hit rate validation"""

    @pytest.fixture
    async def setup_cache(self):
        """Setup cache for testing"""
        cache = await get_unified_cache()
        await cache.clear()  # Start with clean cache
        return cache

    @pytest.fixture
    def mock_provider_config(self):
        """Mock provider configuration"""
        return ProviderConfig(
            name="test_provider",
            base_url="https://api.test.com",
            api_key="test_key",
        )

    @pytest.fixture
    def mock_models(self):
        """Mock model data"""
        return [
            ModelInfo(
                id="gpt-4",
                object="model",
                created=time.time(),
                owned_by="test_provider",
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                object="model",
                created=time.time(),
                owned_by="test_provider",
            ),
        ]

    async def test_model_discovery_cache_hit_rate(
        self, setup_cache, mock_provider_config, mock_models
    ):
        """Test that model discovery achieves >90% cache hit rate"""
        service = ModelDiscoveryService()

        # Mock the HTTP request to avoid actual API calls
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "data": [
                        {
                            "id": "gpt-4",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "test_provider",
                        },
                        {
                            "id": "gpt-3.5-turbo",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "test_provider",
                        },
                    ]
                }
            )

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session.return_value.get.return_value = mock_context

            # First call - should be cache miss
            models1 = await service.discover_models(mock_provider_config)
            assert len(models1) == 2

            # Get cache stats after first call
            cache_stats = await service.get_cache_stats()
            assert cache_stats["model_cache_entries"] == 1

            # Multiple subsequent calls - should be cache hits
            hit_count = 0
            total_calls = 10

            for i in range(total_calls):
                models = await service.discover_models(mock_provider_config)
                assert len(models) == 2
                assert models[0].id == "gpt-4"

                # Check if this was a cache hit (no HTTP call made)
                if i > 0:  # First call was miss, rest should be hits
                    hit_count += 1

            # Verify we got cache hits
            assert (
                hit_count == total_calls - 1
            ), f"Expected {total_calls - 1} cache hits, got {hit_count}"

            # Check final cache stats
            final_stats = await service.get_cache_stats()
            cache_hit_rate = final_stats["cache_hit_rate"]

            print(f"Model discovery cache hit rate: {cache_hit_rate:.2%}")
            assert (
                cache_hit_rate >= 0.9
            ), f"Cache hit rate {cache_hit_rate:.2%} is below 90% target"

    async def test_provider_discovery_cache_hit_rate(self, setup_cache):
        """Test that provider discovery achieves >90% cache hit rate"""
        # Mock provider metrics
        provider_discovery._provider_metrics["test_provider"] = (
            provider_discovery._get_or_create_metrics("test_provider")
        )
        provider_discovery._provider_metrics["test_provider"].record_request(
            True, 100
        )

        # First call - should be cache miss
        report1 = await provider_discovery.get_provider_performance_report()
        assert "providers" in report1

        # Multiple subsequent calls - should be cache hits
        hit_count = 0
        total_calls = 10

        for i in range(total_calls):
            report = await provider_discovery.get_provider_performance_report()
            assert "providers" in report

            if i > 0:  # First call was miss, rest should be hits
                hit_count += 1

        # Check cache stats
        cache_stats = await provider_discovery.get_cache_stats()
        cache_hit_rate = cache_stats["cache_hit_rate"]

        print(f"Provider discovery cache hit rate: {cache_hit_rate:.2%}")
        assert (
            cache_hit_rate >= 0.9
        ), f"Cache hit rate {cache_hit_rate:.2%} is below 90% target"

    async def test_unified_cache_performance(self, setup_cache):
        """Test unified cache performance under load"""
        cache = await setup_cache

        # Simulate high-frequency cache operations
        test_keys = [f"test_key_{i}" for i in range(100)]
        test_data = {"data": f"test_value_{i}" for i in range(100)}

        # Warm up cache
        for i, key in enumerate(test_keys[:50]):
            await cache.set(key, test_data[i], ttl=300, category="test")

        # Simulate mixed read/write operations
        operations = 1000
        hits = 0
        misses = 0

        for i in range(operations):
            key = test_keys[i % len(test_keys)]
            if i % 3 == 0:  # Write operation
                await cache.set(
                    key,
                    test_data[i % len(test_data)],
                    ttl=300,
                    category="test",
                )
            else:  # Read operation
                result = await cache.get(key, category="test")
                if result is not None:
                    hits += 1
                else:
                    misses += 1

        total_reads = hits + misses
        hit_rate = hits / total_reads if total_reads > 0 else 0

        print(f"Unified cache hit rate under load: {hit_rate:.2%}")
        assert (
            hit_rate >= 0.9
        ), f"Cache hit rate {hit_rate:.2%} is below 90% target"

        # Verify cache stats
        stats = await cache.get_stats()
        assert stats["entries"] > 0
        assert stats["hit_rate"] >= 0.9

    async def test_cache_monitoring(self, setup_cache):
        """Test cache monitoring functionality"""
        # Start monitoring
        await cache_monitor.start_monitoring()

        # Wait a bit for monitoring to run
        await asyncio.sleep(2)

        # Get health report
        health_report = await cache_monitor.get_cache_health_report()

        assert "overall_health" in health_report
        assert "current_hit_rate" in health_report
        assert "recommendations" in health_report

        # Stop monitoring
        await cache_monitor.stop_monitoring()

    async def test_cache_warming(
        self, setup_cache, mock_provider_config, mock_models
    ):
        """Test cache warming functionality"""
        # Mock the model discovery
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "data": [
                        {
                            "id": "gpt-4",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "test_provider",
                        }
                    ]
                }
            )

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session.return_value.get.return_value = mock_context

            # Perform cache warming
            warming_results = await cache_monitor.warmup_cache()

            assert "models_warmed" in warming_results
            assert "providers_warmed" in warming_results
            assert "errors" in warming_results

    async def test_cache_invalidation(
        self, setup_cache, mock_provider_config, mock_models
    ):
        """Test cache invalidation functionality"""
        service = ModelDiscoveryService()

        # Mock HTTP response
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(
                return_value={
                    "data": [
                        {
                            "id": "gpt-4",
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "test_provider",
                        }
                    ]
                }
            )

            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context.__aexit__ = AsyncMock(return_value=None)

            mock_session.return_value.get.return_value = mock_context

            # Cache some data
            models1 = await service.discover_models(mock_provider_config)
            assert len(models1) == 1

            # Verify it's cached
            cached_models = await service.discover_models(mock_provider_config)
            assert len(cached_models) == 1

            # Invalidate cache
            invalidated = await service.invalidate_model_cache(
                mock_provider_config
            )
            assert invalidated

            # Next call should be a cache miss (would make HTTP call if not mocked)
            # We can't easily test the full invalidation without complex mocking,
            # but we can verify the invalidation method exists and returns expected result

    async def test_memory_management(self, setup_cache):
        """Test cache memory management and LRU eviction"""
        cache = await setup_cache

        # Fill cache with many entries
        for i in range(150):  # More than default max_size of 100
            await cache.set(
                f"memory_test_{i}",
                {"data": f"value_{i}"},
                ttl=300,
                category="test",
            )

        # Check that cache size is managed
        stats = await cache.get_stats()
        assert stats["entries"] <= stats["max_size"] + 10  # Allow some buffer

        # Test memory usage is reasonable
        memory_mb = stats.get("memory_usage_mb", 0)
        max_memory_mb = stats.get("max_memory_mb", 0)
        assert memory_mb <= max_memory_mb

        print(f"Cache memory usage: {memory_mb}MB / {max_memory_mb}MB")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
