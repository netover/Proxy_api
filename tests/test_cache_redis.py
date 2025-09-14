import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.cache_redis import RedisCacheAdapter
from src.core.unified_config import RedisSettings

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def redis_settings():
    """Provides a default RedisSettings instance for tests."""
    return RedisSettings(enabled=True, host="localhost", port=6379, db=0)

@pytest.fixture
def mock_redis_client():
    """Mocks the redis.asyncio.Redis client."""
    mock_client = AsyncMock()
    mock_client.ping = AsyncMock(return_value=True)
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock()
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.keys = AsyncMock(return_value=[])
    mock_client.close = AsyncMock()
    return mock_client

@pytest_asyncio.fixture
async def redis_adapter(redis_settings, mock_redis_client):
    """Provides an initialized RedisCacheAdapter with a mocked client."""
    with patch('src.core.cache_redis.Redis', return_value=mock_redis_client):
        adapter = RedisCacheAdapter(settings=redis_settings)
        await adapter.start()
        yield adapter
        await adapter.stop()

class TestRedisCacheAdapter:
    """Unit tests for the RedisCacheAdapter."""

    async def test_start_and_stop(self, redis_settings):
        """Test the start and stop methods."""
        with patch('src.core.cache_redis.Redis') as mock_redis_class:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client

            adapter = RedisCacheAdapter(settings=redis_settings)
            await adapter.start()

            mock_redis_class.assert_called_once_with(
                host="localhost", port=6379, db=0, password=None, decode_responses=False
            )
            mock_client.ping.assert_awaited_once()
            assert adapter._redis is not None

            await adapter.stop()
            mock_client.close.assert_awaited_once()
            assert adapter._redis is None

    async def test_get_cache_hit(self, redis_adapter, mock_redis_client):
        """Test a successful cache hit."""
        import orjson
        test_data = {"message": "hello"}
        mock_redis_client.get.return_value = orjson.dumps(test_data)

        result = await redis_adapter.get("test_key")

        mock_redis_client.get.assert_awaited_once_with("llmproxy_cache:test_key")
        assert result == test_data
        assert redis_adapter.hits == 1
        assert redis_adapter.misses == 0

    async def test_get_cache_miss(self, redis_adapter, mock_redis_client):
        """Test a cache miss."""
        mock_redis_client.get.return_value = None

        result = await redis_adapter.get("test_key")

        assert result is None
        assert redis_adapter.hits == 0
        assert redis_adapter.misses == 1

    async def test_set_value(self, redis_adapter, mock_redis_client):
        """Test setting a value in the cache."""
        import orjson
        test_data = {"message": "world"}

        success = await redis_adapter.set("test_key", test_data, ttl=60)

        assert success is True
        mock_redis_client.set.assert_awaited_once_with(
            "llmproxy_cache:test_key", orjson.dumps(test_data), ex=60
        )

    async def test_set_with_default_ttl(self, mock_redis_client, redis_settings):
        """Test setting a value uses the default TTL."""
        import orjson
        test_data = {"data": 123}
        adapter_with_ttl = RedisCacheAdapter(redis_settings, default_ttl=300)
        adapter_with_ttl._redis = mock_redis_client # Manually assign mock

        await adapter_with_ttl.set("test_key_ttl", test_data)

        mock_redis_client.set.assert_awaited_with(
            "llmproxy_cache:test_key_ttl", orjson.dumps(test_data), ex=300
        )

    async def test_delete_key(self, redis_adapter, mock_redis_client):
        """Test deleting a key."""
        success = await redis_adapter.delete("test_key_to_delete")

        assert success is True
        mock_redis_client.delete.assert_awaited_once_with("llmproxy_cache:test_key_to_delete")

    async def test_clear_namespace(self, redis_adapter, mock_redis_client):
        """Test clearing all keys in the namespace."""
        mock_redis_client.keys.return_value = [
            b'llmproxy_cache:key1', b'llmproxy_cache:key2'
        ]

        success = await redis_adapter.clear()

        assert success is True
        mock_redis_client.keys.assert_awaited_once_with("llmproxy_cache:*")
        mock_redis_client.delete.assert_awaited_once_with(
            b'llmproxy_cache:key1', b'llmproxy_cache:key2'
        )

    async def test_get_or_set_cache_hit(self, redis_adapter, mock_redis_client):
        """Test get_or_set when the value is in the cache."""
        import orjson
        mock_redis_client.get.return_value = orjson.dumps({"data": "from_cache"})
        getter_func = AsyncMock()

        result = await redis_adapter.get_or_set("hit_key", getter_func)

        assert result == {"data": "from_cache"}
        getter_func.assert_not_awaited()

    async def test_get_or_set_cache_miss(self, redis_adapter, mock_redis_client):
        """Test get_or_set when the value is not in the cache."""
        mock_redis_client.get.return_value = None
        getter_func = AsyncMock(return_value={"data": "from_getter"})

        result = await redis_adapter.get_or_set("miss_key", getter_func, ttl=120)

        assert result == {"data": "from_getter"}
        getter_func.assert_awaited_once()
        mock_redis_client.set.assert_awaited_once()

    async def test_get_stats_connected(self, redis_adapter, mock_redis_client):
        """Test getting stats when connected."""
        mock_redis_client.info.return_value = {
            "redis_version": "7.2.0",
            "used_memory_human": "1.2M",
            "db0": {"keys": 10},
        }

        stats = await redis_adapter.get_stats()

        assert stats["connected"] is True
        assert stats["redis_version"] == "7.2.0"
        assert stats["total_keys"] == 10
        assert stats["hits"] == 0
