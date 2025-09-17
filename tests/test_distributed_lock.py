"""
Tests for the DistributedLock and its integration with ConsolidatedCacheManager.
Verifies that the distributed lock prevents race conditions during cache warming.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.core.consolidated_cache_enhanced import (
    ConsolidatedCacheManager,
    DistributedLock,
)

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def mock_redis_client():
    """Fixture to create a mock of the redis.asyncio.Redis client."""
    mock_redis = AsyncMock()

    # Mock the 'set' method to simulate lock acquisition
    # Use a dictionary to store lock state
    locks = {}

    async def set_lock(key, value, nx, ex):
        if nx and key not in locks:
            locks[key] = value
            return True
        return False

    async def delete_lock(key):
        if key in locks:
            del locks[key]
        return 1

    mock_redis.set.side_effect = set_lock
    mock_redis.delete.side_effect = delete_lock
    mock_redis.ping.return_value = True

    return mock_redis, locks


@pytest_asyncio.fixture
async def cache_manager(mock_redis_client):
    """Fixture to create a ConsolidatedCacheManager with a mocked Redis client."""
    mock_redis, _ = mock_redis_client

    # Create a mock for the unified cache
    mock_unified_cache = AsyncMock()
    mock_unified_cache.get_many.return_value = {}

    # Create a mock warmer
    mock_warmer = AsyncMock()

    # Create the manager instance
    manager = ConsolidatedCacheManager(redis_url="redis://mock")

    # Manually inject mocks
    manager.redis = mock_redis
    manager._cache = mock_unified_cache
    manager._warmer = mock_warmer
    manager._running = True  # Mark as running

    return manager


async def test_distributed_lock_acquires_and_releases(mock_redis_client):
    """Test that the lock can be acquired and is released properly."""
    mock_redis, locks = mock_redis_client
    lock_key = "test_lock"

    assert not locks  # Ensure no locks at the start

    lock = DistributedLock(mock_redis, lock_key, timeout=10)
    async with lock:
        # Check that the lock is present in our mock storage
        assert lock_key in locks

    # Check that the lock was released upon exiting the context
    assert not locks


async def test_distributed_lock_blocks_concurrent_access(mock_redis_client):
    """Test that a second process must wait for the first to release the lock."""
    mock_redis, locks = mock_redis_client
    lock_key = "test_lock_concurrent"

    lock1 = DistributedLock(mock_redis, lock_key, timeout=10)
    lock2 = DistributedLock(mock_redis, lock_key, timeout=10)

    async with lock1:
        assert lock_key in locks

        # Try to acquire the lock again in a separate task
        # It should block until the first lock is released
        acquire_task = asyncio.create_task(lock2.__aenter__())

        # Give the task a moment to run and block
        await asyncio.sleep(0.2)
        assert not acquire_task.done()  # It should be waiting for the lock

    # After lock1 is released, lock2 should be able to acquire it
    await acquire_task
    assert lock_key in locks  # Now lock2 holds it

    await lock2.__aexit__(None, None, None)
    assert not locks  # And now it's released


async def test_warm_cache_batch_uses_distributed_lock(cache_manager, mock_redis_client):
    """Verify that warm_cache_batch uses the distributed lock."""
    mock_redis, locks = mock_redis_client

    keys_to_warm = ["key1", "key2"]
    category = "test_cat"
    batch_id = hash(tuple(sorted(keys_to_warm)))
    expected_lock_key = f"lock:warm_batch:{category}:{batch_id}"

    # Mock the getter function
    getter_func = AsyncMock(return_value="warmed_value")

    # Run the batch warming
    await cache_manager.warm_cache_batch(keys_to_warm, getter_func, category, ttl=3600)

    # Assert that the lock was set and then deleted
    mock_redis.set.assert_called_once_with(expected_lock_key, "locked", nx=True, ex=60)
    mock_redis.delete.assert_called_once_with(expected_lock_key)


async def test_warm_cache_batch_concurrent_calls(cache_manager, mock_redis_client):
    """Simulate two instances calling warm_cache_batch for the same batch concurrently."""
    mock_redis, _ = mock_redis_client

    keys = ["keyA", "keyB"]
    category = "concurrent_cat"
    getter_func = AsyncMock(side_effect=lambda k: f"value_for_{k}")

    # We will track how many times the getter_func is called.
    # If the lock works, it should only be called for the number of keys, not twice that.

    # The first call will acquire the lock and proceed.
    # The second call should acquire the lock *after* the first is done,
    # at which point the keys are already cached, so it should do nothing.

    async def run_warming():
        # The mock cache's get_many will initially return no existing keys
        cache_manager._cache.get_many.return_value = {}

        # After the first run, the keys will be in the cache
        async def get_many_side_effect(keys, cat):
            # On the first call, nothing is cached
            if get_many_side_effect.call_count == 1:
                get_many_side_effect.call_count += 1
                return {}
            # On subsequent calls, everything is cached
            return {k: "cached" for k in keys}

        get_many_side_effect.call_count = 1
        cache_manager._cache.get_many.side_effect = get_many_side_effect

        await cache_manager.warm_cache_batch(keys, getter_func, category, ttl=60)

    # Simulate two concurrent calls
    task1 = asyncio.create_task(run_warming())
    task2 = asyncio.create_task(run_warming())

    await asyncio.gather(task1, task2)

    # The getter function should have been called only for the initial set of keys,
    # because the second call should have found the keys already cached by the first.
    assert getter_func.call_count == len(keys)

    # The underlying cache set method should have been called only for the initial keys
    assert cache_manager._cache.set.call_count == len(keys)
