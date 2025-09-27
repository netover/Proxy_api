"""
Pytest configuration and fixtures for LLM Proxy API testing.
"""

import asyncio
import os
import pytest
import tempfile
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.config.models import UnifiedConfig, ProviderConfig
from src.core.unified_config import config_manager
from src.core.app_state import app_state
from src.core.providers.factory import provider_factory
from src.core.cache.redis_cache import DistributedCacheManager
from src.core.rate_limiter_redis import DistributedRateLimiter


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_config():
    """Create a test configuration."""
    return UnifiedConfig(
        app={"name": "Test API", "version": "1.0.0"},
        providers=[
            ProviderConfig(
                name="test_openai",
                type="openai",
                api_key_env="TEST_OPENAI_KEY",
                models=["gpt-3.5-turbo"],
                enabled=True
            )
        ],
        caching={
            "enabled": True,
            "redis_url": "redis://localhost:6379",
            "response_cache": {"max_size_mb": 10, "ttl": 300, "compression": True},
            "summary_cache": {"max_size_mb": 5, "ttl": 600, "compression": True}
        },
        rate_limit={
            "requests_per_window": 100,
            "window_seconds": 60,
            "redis_url": "redis://localhost:6379",
            "strategy": "sliding_window"
        }
    )


@pytest.fixture
async def app_state_fixture(test_config):
    """Initialize app state for testing."""
    try:
        await app_state.initialize(test_config)
        yield app_state
    finally:
        await app_state.shutdown()


@pytest.fixture
async def provider_factory_fixture(test_config):
    """Initialize provider factory for testing."""
    try:
        # Set dummy API keys for testing
        os.environ['TEST_OPENAI_KEY'] = 'dummy_key_for_testing'

        providers = await provider_factory.initialize(test_config)
        yield provider_factory
    finally:
        await provider_factory.shutdown()


@pytest.fixture
async def cache_manager_fixture(test_config):
    """Initialize cache manager for testing."""
    try:
        manager = DistributedCacheManager()
        await manager.initialize(test_config.caching)
        yield manager
    finally:
        await manager.shutdown()


@pytest.fixture
async def rate_limiter_fixture(test_config):
    """Initialize rate limiter for testing."""
    try:
        limiter = DistributedRateLimiter()
        await limiter.initialize(test_config.rate_limit)
        yield limiter
    finally:
        await limiter.shutdown()


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = {
        "app": {"name": "Test API", "version": "1.0.0"},
        "providers": [
            {
                "name": "test_provider",
                "type": "openai",
                "api_key_env": "TEST_KEY",
                "models": ["gpt-3.5-turbo"],
                "enabled": True
            }
        ]
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_provider_response():
    """Mock provider response for testing."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is a test response"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        },
        "model": "gpt-3.5-turbo"
    }


@pytest.fixture
def sample_chat_request():
    """Sample chat completion request for testing."""
    return {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }


@pytest.fixture
def sample_embedding_request():
    """Sample embedding request for testing."""
    return {
        "model": "text-embedding-ada-002",
        "input": "Test input for embedding"
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set test API keys
    os.environ['TEST_OPENAI_KEY'] = 'sk-test123456789'
    os.environ['TEST_ANTHROPIC_KEY'] = 'sk-ant123456789'
    os.environ['TEST_AZURE_KEY'] = 'azure-test-key'

    yield

    # Cleanup environment
    for key in ['TEST_OPENAI_KEY', 'TEST_ANTHROPIC_KEY', 'TEST_AZURE_KEY']:
        os.environ.pop(key, None)


@pytest.fixture
def redis_available():
    """Check if Redis is available for testing."""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        return True
    except:
        return False


@pytest.fixture
async def skip_if_no_redis(redis_available):
    """Skip test if Redis is not available."""
    if not redis_available:
        pytest.skip("Redis not available for testing")


# Redis Mock Fixtures
@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client for testing."""
    mock_client = AsyncMock()

    # Mock basic Redis operations
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.setex.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False
    mock_client.keys.return_value = []
    mock_client.zadd.return_value = 1
    mock_client.zcount.return_value = 0
    mock_client.zremrangebyscore.return_value = 0
    mock_client.zcard.return_value = 0
    mock_client.info.return_value = {"used_memory_human": "1M"}
    mock_client.ttl.return_value = 300

    # Configure zcount to return a value based on the range
    def mock_zcount(key, min_score, max_score):
        # For testing, return a count based on the max_score
        # This is a simple mock - in real implementation would track actual values
        return 1  # Return 1 for testing purposes

    mock_client.zcount.side_effect = mock_zcount

    # Mock zadd to track added values for zcount
    zadd_data = {}
    original_zadd = mock_client.zadd

    async def mock_zadd(key, mapping):
        # Call original mock behavior
        result = await original_zadd(key, mapping)

        # Track the values for zcount
        if key not in zadd_data:
            zadd_data[key] = []
        zadd_data[key].extend(mapping.values())

        return result

    mock_client.zadd = mock_zadd

    # Update zcount to return the actual count of values
    def updated_mock_zcount(key, min_score, max_score):
        if key in zadd_data:
            # Count values within the range
            count = sum(1 for val in zadd_data[key] if min_score <= val <= max_score)
            return count
        return 0

    mock_client.zcount.side_effect = updated_mock_zcount

    return mock_client


@pytest.fixture
def redis_mock_context(mock_redis_client):
    """Context manager for Redis mocking."""
    def mock_from_url(url, **kwargs):
        return mock_redis_client

    def mock_asyncio_from_url(url, **kwargs):
        return mock_redis_client

    with patch('redis.from_url', side_effect=mock_from_url):
        with patch('redis.Redis', return_value=mock_redis_client):
            with patch('redis.asyncio.from_url', side_effect=mock_asyncio_from_url):
                with patch('redis.asyncio.Redis', return_value=mock_redis_client):
                    yield mock_redis_client


@pytest.fixture
def mock_redis_asyncio():
    """Mock redis.asyncio module."""
    with patch('redis.asyncio') as mock_redis:
        # Create mock Redis client
        mock_client = AsyncMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.setex.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = False
        mock_client.keys.return_value = []
        mock_client.zadd.return_value = 1
        mock_client.zcount.return_value = 0
        mock_client.zremrangebyscore.return_value = 0
        mock_client.zcard.return_value = 0
        mock_client.info.return_value = {"used_memory_human": "1M"}
        mock_client.ttl.return_value = 300
        mock_client.close.return_value = None

        mock_redis.from_url.return_value = mock_client
        yield mock_redis