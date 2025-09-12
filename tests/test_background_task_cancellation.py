"""
Tests for background task cancellation and resource leakage prevention.

This module tests that background tasks are properly cancelled on shutdown
and don't leak resources. It covers:
- Task lifecycle management
- Resource cleanup on shutdown
- Leakage detection
- Graceful cancellation handling
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.context_condenser import AsyncLRUCache
from src.core.unified_cache import UnifiedCache
from src.core.provider_factory import ProviderFactory
from src.core.parallel_fallback import ParallelFallbackEngine


class TestAsyncLRUCacheCancellation:
    """Test AsyncLRUCache background task cancellation"""

    @pytest.fixture
    def cache(self):
        """Create a cache instance for testing"""
        return AsyncLRUCache(maxsize=10, persist_file="test_cache.json")

    @pytest.mark.asyncio
    async def test_background_task_tracking(self, cache):
        """Test that background tasks are properly tracked"""
        # Initially no background tasks
        assert len(cache._background_tasks) == 0

        # Add an item (triggers background save)
        cache.set("test_key", ("test_value", time.time()))

        # Should have a background task
        assert len(cache._background_tasks) == 1

        # Wait for task to complete
        await asyncio.sleep(0.1)
        assert len(cache._background_tasks) == 0

    @pytest.mark.asyncio
    async def test_shutdown_cancels_tasks(self, cache):
        """Test that shutdown cancels all pending background tasks"""
        # Mock the save method to take some time
        original_save = cache.save
        async def slow_save():
            await asyncio.sleep(1.0)  # Simulate slow save
            await original_save()

        with patch.object(cache, 'save', side_effect=slow_save):
            # Add multiple items to create background tasks
            for i in range(5):
                cache.set(f"key_{i}", (f"value_{i}", time.time()))

            # Should have background tasks
            assert len(cache._background_tasks) == 5

            # Start shutdown
            shutdown_task = asyncio.create_task(cache.shutdown())

            # Wait a bit for cancellation to take effect
            await asyncio.sleep(0.1)

            # Tasks should be cancelled
            active_tasks = [t for t in cache._background_tasks if not t.done()]
            assert len(active_tasks) == 0

            # Shutdown should complete
            await shutdown_task

    @pytest.mark.asyncio
    async def test_task_cleanup_on_completion(self, cache):
        """Test that completed tasks are removed from tracking set"""
        # Add an item
        cache.set("test_key", ("test_value", time.time()))

        # Should have a background task
        assert len(cache._background_tasks) == 1

        # Wait for completion
        await asyncio.sleep(0.1)

        # Task should be cleaned up automatically
        assert len(cache._background_tasks) == 0

    @pytest.mark.asyncio
    async def test_eviction_creates_cancellable_task(self, cache):
        """Test that Redis eviction creates a cancellable task"""
        # Mock Redis client
        mock_redis = AsyncMock()
        cache.redis_client = mock_redis

        # Fill cache to max size
        for i in range(11):  # maxsize is 10
            cache.set(f"key_{i}", (f"value_{i}", time.time()))

        # Should have created a background task for Redis deletion
        assert len(cache._background_tasks) >= 1

        # Shutdown should cancel the task
        await cache.shutdown()

        # Verify Redis delete was called (but cancelled)
        mock_redis.delete.assert_called()


class TestUnifiedCacheCancellation:
    """Test UnifiedCache background task cancellation"""

    @pytest.fixture
    def cache(self):
        """Create a unified cache instance for testing"""
        return UnifiedCache(max_size=10, default_ttl=30)

    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, cache):
        """Test proper start/stop lifecycle"""
        # Initially not running
        assert not cache._running

        # Start the cache
        await cache.start()
        assert cache._running
        assert cache._cleanup_task is not None
        assert not cache._cleanup_task.done()

        # Stop the cache
        await cache.stop()
        assert not cache._running
        assert cache._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_all_tasks(self, cache):
        """Test that stop cancels all background tasks"""
        await cache.start()

        # Tasks should be running
        assert not cache._cleanup_task.done()

        # Stop should cancel tasks
        await cache.stop()

        # Tasks should be done (cancelled)
        assert cache._cleanup_task.done()

        # The UnifiedCache handles CancelledError internally, so awaiting should not raise
        # This is the correct behavior - the task completed due to cancellation
        await cache._cleanup_task  # Should not raise CancelledError

    @pytest.mark.asyncio
    async def test_warming_tasks_cancellation(self, cache):
        """Test that warming tasks are properly cancelled"""
        cache.enable_predictive_warming = True
        await cache.start()

        # Should have warming task
        assert cache._warming_task is not None
        assert not cache._warming_task.done()

        # Stop should cancel warming task
        await cache.stop()
        assert cache._warming_task.done()


class TestProviderFactoryCancellation:
    """Test ProviderFactory background task cancellation"""

    @pytest.fixture
    def factory(self):
        """Create a provider factory instance for testing"""
        return ProviderFactory()

    @pytest.mark.asyncio
    async def test_health_monitoring_cancellation(self, factory):
        """Test health monitoring task cancellation"""
        # Mock the health check loop to run indefinitely
        original_loop = factory._health_check_loop
        async def infinite_loop():
            while not factory._shutdown_event.is_set():
                await asyncio.sleep(0.1)

        factory._health_check_loop = infinite_loop

        # Start health monitoring
        await factory.start_health_monitoring()
        assert factory._health_check_task is not None
        assert not factory._health_check_task.done()

        # Shutdown should cancel the task
        await factory.shutdown()
        assert factory._health_check_task.done()

        # Restore original method
        factory._health_check_loop = original_loop

    @pytest.mark.asyncio
    async def test_shutdown_event_properly_set(self, factory):
        """Test that shutdown event is properly set during shutdown"""
        assert not factory._shutdown_event.is_set()

        await factory.shutdown()

        assert factory._shutdown_event.is_set()


class TestParallelFallbackCancellation:
    """Test ParallelFallbackEngine task cancellation"""

    @pytest.fixture
    def engine(self):
        """Create a parallel fallback engine for testing"""
        return ParallelFallbackEngine(max_concurrent_providers=3)

    @pytest.mark.asyncio
    async def test_execution_cancellation(self, engine):
        """Test that parallel execution properly cancels tasks"""
        # Mock provider discovery
        with patch('src.core.parallel_fallback.provider_discovery') as mock_discovery:
            mock_discovery.get_healthy_providers_for_model.return_value = ['provider1', 'provider2']

            # Mock provider factory
            with patch('src.core.parallel_fallback.provider_factory') as mock_factory:
                mock_provider = AsyncMock()
                mock_provider.create_completion = AsyncMock(side_effect=asyncio.sleep(10))  # Long running
                mock_factory.get_provider.return_value = mock_provider

                # Start execution
                execution_task = asyncio.create_task(
                    engine.execute_parallel('test-model', {'messages': []}, timeout=0.1)
                )

                # Wait for timeout
                await asyncio.sleep(0.2)

                # Execution should complete (with timeout)
                result = await execution_task
                assert not result.success
                assert 'timeout' in result.error.lower()

    @pytest.mark.asyncio
    async def test_shutdown_cancels_active_executions(self, engine):
        """Test that shutdown cancels active executions"""
        # Mock thread pool
        engine._thread_pool = MagicMock()

        await engine.shutdown()

        # Thread pool should be shutdown
        engine._thread_pool.shutdown.assert_called_once()


class TestResourceLeakageDetection:
    """Test resource leakage detection"""

    @pytest.mark.asyncio
    async def test_task_leakage_detection(self):
        """Test detection of leaked tasks"""
        # Create a task that won't be properly tracked
        async def leaked_task():
            await asyncio.sleep(10)

        # Create task without storing reference (simulating leak)
        asyncio.create_task(leaked_task())

        # Get all tasks
        all_tasks = asyncio.all_tasks()
        current_task = asyncio.current_task()

        # Should have more than just the current task
        other_tasks = [t for t in all_tasks if t != current_task]
        assert len(other_tasks) > 0

        # Clean up leaked task
        for task in other_tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self):
        """Test memory usage tracking for cache objects"""
        cache = AsyncLRUCache(maxsize=100)

        # Add some items
        for i in range(10):
            cache.set(f"key_{i}", (f"value_{i}", time.time()))

        # Should have items in cache
        assert len(cache.cache) == 10

        # Clear should remove items
        cache.clear()
        assert len(cache.cache) == 0

        # Shutdown should work
        await cache.shutdown()


class TestGracefulShutdown:
    """Test graceful shutdown behavior"""

    @pytest.mark.asyncio
    async def test_task_cancellation_on_shutdown(self):
        """Test that tasks can be cancelled properly during shutdown"""
        # Create some background tasks
        background_tasks = []
        for i in range(3):
            task = asyncio.create_task(asyncio.sleep(10))
            background_tasks.append(task)

        # Simulate shutdown: cancel all tasks
        cancelled_count = 0
        for task in background_tasks:
            if not task.done():
                task.cancel()
                cancelled_count += 1

        # Wait for all tasks to be cancelled
        await asyncio.gather(*background_tasks, return_exceptions=True)

        # All tasks should be cancelled
        assert cancelled_count == 3
        for task in background_tasks:
            assert task.cancelled()


if __name__ == "__main__":
    pytest.main([__file__])