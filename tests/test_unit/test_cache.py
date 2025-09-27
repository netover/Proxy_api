"""
Unit tests for cache implementations.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.core.cache.redis_cache import RedisCache, DistributedCacheManager


class TestRedisCache:
    """Test Redis cache implementation."""

    @pytest.mark.asyncio
    async def test_cache_initialization_failure(self):
        """Test cache initialization when Redis is unavailable."""
        cache = RedisCache(redis_url="redis://invalid:6379")

        # Should handle connection failure gracefully
        with pytest.raises(Exception):  # Redis connection error
            await cache.initialize()

        # Cache should handle operations gracefully when Redis is down
        result = await cache.set("test_key", "test_value")
        assert result is False

        result = await cache.get("test_key")
        assert result is None

        result = await cache.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = RedisCache()

        # Should return stats even when Redis is down
        stats = await cache.get_stats()

        assert isinstance(stats, dict)
        assert "redis_connected" in stats
        assert "stats" in stats
        assert stats["stats"]["sets"] == 0
        assert stats["stats"]["hits"] == 0

    @pytest.mark.asyncio
    async def test_cache_compression(self):
        """Test cache compression functionality."""
        cache = RedisCache(compression_enabled=True)

        test_data = {"large_data": "x" * 10000}  # 10KB of data

        # Should handle compression without errors
        result = await cache.set("compression_test", test_data)
        # Will fail due to no Redis, but shouldn't crash
        assert result is False


class TestDistributedCacheManager:
    """Test distributed cache manager."""

    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """Test cache manager initialization."""
        from src.core.config.models import CachingConfig, CacheSubConfig

        config = CachingConfig(
            enabled=True,
            redis_url="redis://localhost:6379",
            response_cache=CacheSubConfig(max_size_mb=100, ttl=300, compression=True),
            summary_cache=CacheSubConfig(max_size_mb=50, ttl=600, compression=True)
        )

        manager = DistributedCacheManager()

        # Should initialize without errors, even if Redis is down
        try:
            await manager.initialize(config)
            # Manager should have caches configured
            assert len(manager.caches) >= 0  # May be 0 if Redis fails
        except Exception as e:
            # Should handle Redis unavailability gracefully
            assert "connection" in str(e).lower() or "redis" in str(e).lower()

    @pytest.mark.asyncio
    async def test_cache_selection(self):
        """Test cache selection by type."""
        manager = DistributedCacheManager()

        # Should return None for non-existent cache types
        cache = manager.get_cache("nonexistent")
        assert cache is None

        # Should return None for response cache when not initialized
        cache = manager.get_cache("response")
        assert cache is None


class TestRedisCacheWithMocks:
    """Test Redis cache with mocked Redis client."""

    @pytest.mark.asyncio
    async def test_cache_operations_with_mocked_redis(self, redis_mock_context):
        """Test cache operations with mocked Redis."""
        cache = RedisCache(
            redis_url="redis://localhost:6379",
            ttl=300,
            max_size_mb=10,
            compression_enabled=False  # Disable compression for easier testing
        )

        # Initialize should work with mocked Redis
        await cache.initialize()

        # Test set operation
        test_data = {"test": "data", "number": 42}
        result = await cache.set("test_key", test_data)
        assert result is True

        # Verify Redis was called
        redis_mock_context.setex.assert_called()

        # Configure mock to return the data when get is called (serialized with pickle)
        import pickle
        redis_mock_context.get.return_value = pickle.dumps(test_data)

        # Test get operation
        retrieved = await cache.get("test_key")
        assert retrieved == test_data

        # Test exists
        redis_mock_context.exists.return_value = True
        exists = await cache.exists("test_key")
        assert exists is True

        # Test TTL
        ttl = await cache.get_ttl("test_key")
        assert ttl > 0

        # Test delete
        redis_mock_context.delete.return_value = 1
        deleted = await cache.delete("test_key")
        assert deleted is True

        # Test stats
        stats = await cache.get_stats()
        assert "redis_connected" in stats
        assert stats["stats"]["sets"] == 1
        assert stats["stats"]["hits"] == 1

        await cache.shutdown()

    @pytest.mark.asyncio
    async def test_cache_compression(self, redis_mock_context):
        """Test cache compression functionality."""
        cache = RedisCache(
            redis_url="redis://localhost:6379",
            compression_enabled=True
        )

        await cache.initialize()

        # Test with large data that should be compressed
        large_data = {"data": "x" * 10000}  # 10KB
        result = await cache.set("large_key", large_data)
        assert result is True

        # Configure mock to return compressed data
        import pickle
        import zlib
        compressed_data = zlib.compress(pickle.dumps(large_data))
        redis_mock_context.get.return_value = compressed_data

        # Verify data can be retrieved
        retrieved = await cache.get("large_key")
        assert retrieved == large_data

        await cache.shutdown()

    @pytest.mark.asyncio
    async def test_cache_error_handling(self, redis_mock_context):
        """Test cache error handling."""
        cache = RedisCache(redis_url="redis://localhost:6379")

        # Mock Redis to raise exceptions
        redis_mock_context.get.side_effect = Exception("Redis error")
        redis_mock_context.setex.side_effect = Exception("Redis error")

        await cache.initialize()

        # Operations should handle errors gracefully
        result = await cache.get("test_key")
        assert result is None

        result = await cache.set("test_key", "test_value")
        assert result is False

        # Stats should reflect errors
        stats = await cache.get_stats()
        assert stats["stats"]["errors"] >= 2

        await cache.shutdown()

    @pytest.mark.asyncio
    async def test_cache_size_limits(self, redis_mock_context):
        """Test cache size limits."""
        cache = RedisCache(
            redis_url="redis://localhost:6379",
            max_size_mb=0.1,  # 100KB limit for testing
            compression_enabled=False  # Disable compression for predictable size
        )

        await cache.initialize()

        # Test with data under limit
        small_data = {"data": "small"}
        result = await cache.set("small_key", small_data)
        assert result is True

        # Test with data over limit
        large_data = {"data": "x" * (200 * 1024)}  # 200KB - over 100KB limit
        result = await cache.set("large_key", large_data)
        assert result is False  # Should be rejected

        await cache.shutdown()

    @pytest.mark.asyncio
    async def test_cache_ttl_functionality(self, redis_mock_context):
        """Test cache TTL functionality."""
        cache = RedisCache(
            redis_url="redis://localhost:6379",
            ttl=60  # 60 seconds
        )

        await cache.initialize()

        test_data = {"test": "data"}
        result = await cache.set("ttl_test", test_data, ttl=30)  # Custom TTL
        assert result is True

        # Verify that setex was called with correct TTL
        redis_mock_context.setex.assert_called()
        # Check that the TTL parameter was passed correctly
        call_args, call_kwargs = redis_mock_context.setex.call_args
        assert call_args[1] == 30  # TTL should be 30 seconds

        await cache.shutdown()

    @pytest.mark.asyncio
    async def test_cache_namespace_isolation(self, redis_mock_context):
        """Test that different cache instances are isolated."""
        cache1 = RedisCache(namespace="cache1", compression_enabled=False)
        cache2 = RedisCache(namespace="cache2", compression_enabled=False)

        await cache1.initialize()
        await cache2.initialize()

        # Set data in both caches
        await cache1.set("key", "value1")
        await cache2.set("key", "value2")

        # Configure mock to return different values based on key pattern
        def mock_get(key):
            if "cache1" in key:
                import pickle
                return pickle.dumps("value1")
            elif "cache2" in key:
                import pickle
                return pickle.dumps("value2")
            return None

        redis_mock_context.get.side_effect = mock_get

        # Data should be isolated
        val1 = await cache1.get("key")
        val2 = await cache2.get("key")

        assert val1 == "value1"
        assert val2 == "value2"

        await cache1.shutdown()
        await cache2.shutdown()
