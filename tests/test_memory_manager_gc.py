"""
Tests for the SmartContextManager.
Verifies LRU eviction, GC triggering, and thread-safe context management.
"""

import asyncio
import gc
from unittest.mock import patch, MagicMock

import pytest

from src.core.memory_manager import SmartContextManager, get_memory_manager, shutdown_memory_manager, initialize_memory_manager

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
async def manager():
    """Fixture to provide a clean SmartContextManager instance for each test."""
    # Ensure a fresh manager for each test
    await shutdown_memory_manager()
    manager = SmartContextManager(max_size=10)
    return manager


async def test_add_and_get_context(manager: SmartContextManager):
    """Test basic adding and retrieving of contexts."""
    session_id = "session_1"
    context_data = {"user": "test", "data": [1, 2, 3]}

    await manager.add_context(session_id, context_data)
    retrieved_context = await manager.get_context(session_id)

    assert retrieved_context is not None
    assert retrieved_context == context_data
    stats = manager.get_stats()
    assert stats["current_size"] == 1


async def test_lru_eviction(manager: SmartContextManager):
    """Test that the least recently used context is evicted when max_size is reached."""
    # Fill the manager to its max size
    for i in range(10):
        await manager.add_context(f"session_{i}", {"id": i})

    stats = manager.get_stats()
    assert stats["current_size"] == 10

    # Access session_0 to make it the most recently used for a moment, then access others
    await manager.get_context("session_0")
    for i in range(1, 10):
        await manager.get_context(f"session_{i}")

    # Now, session_0 is the least recently used. Add one more context.
    await manager.add_context("session_10", {"id": 10})

    # Check that the manager size is still 10
    stats = manager.get_stats()
    assert stats["current_size"] == 10

    # Check that session_0 was evicted
    retrieved_context = await manager.get_context("session_0")
    assert retrieved_context is None

    # Check that the new session is present
    retrieved_context = await manager.get_context("session_10")
    assert retrieved_context is not None


async def test_gc_triggering(manager: SmartContextManager):
    """Test that garbage collection is triggered when the threshold is exceeded."""
    # The GC threshold is 8 (80% of 10)
    with patch('gc.collect') as mock_gc_collect:
        # Add items up to the threshold
        for i in range(8):
            await manager.add_context(f"session_{i}", {"id": i})

        # GC should not have been called yet
        mock_gc_collect.assert_not_called()

        # Add one more item to cross the threshold
        await manager.add_context("session_8", {"id": 8})

        # Now GC should have been called
        mock_gc_collect.assert_called_once_with(2)


async def test_get_non_existent_context(manager: SmartContextManager):
    """Test that getting a non-existent context returns None."""
    retrieved_context = await manager.get_context("non_existent_session")
    assert retrieved_context is None


async def test_remove_context(manager: SmartContextManager):
    """Test removing a context."""
    session_id = "session_to_remove"
    await manager.add_context(session_id, {"id": "remove_me"})

    stats = manager.get_stats()
    assert stats["current_size"] == 1

    removed = await manager.remove_context(session_id)
    assert removed is True

    stats = manager.get_stats()
    assert stats["current_size"] == 0

    retrieved_context = await manager.get_context(session_id)
    assert retrieved_context is None


async def test_concurrent_add(manager: SmartContextManager):
    """Test that concurrent additions are handled correctly and do not exceed max_size."""
    # Concurrently add more items than the manager can hold
    tasks = [manager.add_context(f"concurrent_session_{i}", {"id": i}) for i in range(20)]
    await asyncio.gather(*tasks)

    stats = manager.get_stats()
    assert stats["current_size"] == 10 # Should not exceed max_size


async def test_global_instance_management():
    """Test the singleton pattern of the global manager."""
    # Ensure we start clean
    await shutdown_memory_manager()

    manager1 = get_memory_manager()
    manager2 = get_memory_manager()

    assert manager1 is manager2

    # Test initialization
    init_manager = await initialize_memory_manager()
    assert init_manager is manager1

    # Test shutdown
    await shutdown_memory_manager()

    # After shutdown, getting the manager should create a new instance
    new_manager = get_memory_manager()
    assert new_manager is not manager1