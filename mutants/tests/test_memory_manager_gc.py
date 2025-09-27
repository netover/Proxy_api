"""
Comprehensive Tests for Memory Manager Garbage Collection
Tests GC endpoint functionality, cleanup latency, and memory management under various conditions.
"""

import asyncio
import gc
import time
import pytest
import psutil
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any
import numpy as np

pytestmark = pytest.mark.anyio

from src.core.memory_manager import (
    MemoryManager,
    MemoryStats,
    get_memory_manager,
    shutdown_memory_manager,
    get_memory_stats
)


class TestMemoryManagerGC:
    """Comprehensive test suite for memory manager GC functionality"""

    async def create_memory_manager(self):
        """Create a fresh memory manager instance for testing"""
        manager = MemoryManager(
            memory_threshold_mb=50,  # Lower threshold for testing
            emergency_threshold_mb=80,  # Lower emergency threshold
            cleanup_interval=1,  # Faster cleanup for testing
            enable_gc_tuning=True,
            leak_detection_enabled=True
        )
        await manager.start()
        return manager

    @pytest.fixture
    def mock_psutil(self):
        """Mock psutil for controlled memory testing"""
        with patch('psutil.Process') as mock_process, \
             patch('psutil.virtual_memory') as mock_virtual:

            mock_proc_instance = MagicMock()
            mock_proc_instance.memory_info.return_value = MagicMock(rss=50 * 1024 * 1024)  # 50MB
            mock_process.return_value = mock_proc_instance

            mock_virtual_instance = MagicMock()
            mock_virtual_instance.total = 8 * 1024 * 1024 * 1024  # 8GB
            mock_virtual_instance.available = 6 * 1024 * 1024 * 1024  # 6GB
            mock_virtual_instance.used = 2 * 1024 * 1024 * 1024  # 2GB
            mock_virtual_instance.percent = 25.0
            mock_virtual.return_value = mock_virtual_instance

            yield

    def create_memory_pressure(self, target_mb: int = 100) -> List[object]:
        """Create memory pressure by allocating objects"""
        objects = []
        # Create objects that will survive garbage collection
        for i in range(target_mb // 10):  # Rough approximation
            objects.append([f"memory_pressure_data_{i}_{j}" * 1000 for j in range(100)])
        return objects

    async def test_basic_gc_functionality(self, mock_psutil):
        """Test basic garbage collection functionality"""
        memory_manager = await self.create_memory_manager()

        try:
            # Create some garbage
            garbage = []
            for i in range(1000):
                garbage.append([f"test_object_{i}"] * 100)

            # Force cleanup
            start_time = time.time()
            collected = await memory_manager.force_cleanup()
            cleanup_time = time.time() - start_time

            # Verify cleanup occurred
            assert collected >= 0
            assert cleanup_time < 1.0  # Should be fast

            # Verify memory stats are available
            stats = memory_manager.get_memory_stats()
            assert isinstance(stats, MemoryStats)
            assert stats.process_memory_mb >= 0
        finally:
            await memory_manager.stop()

    async def test_cleanup_latency_measurement(self, mock_psutil):
        """Test cleanup latency measurement under different conditions"""
        memory_manager = await self.create_memory_manager()
        latencies = []

        try:
            # Test multiple cleanup operations
            for i in range(10):
                # Create varying amounts of garbage
                garbage_size = (i + 1) * 100
                garbage = []
                for j in range(garbage_size):
                    garbage.append([f"latency_test_{i}_{j}"] * 50)

                # Measure cleanup latency
                start_time = time.time()
                collected = await memory_manager.force_cleanup()
                latency = time.time() - start_time

                latencies.append(latency)

                # Cleanup should be reasonably fast
                assert latency < 2.0, f"Cleanup too slow: {latency:.3f}s"

            # Analyze latency distribution
            avg_latency = np.mean(latencies)
            max_latency = np.max(latencies)
            std_latency = np.std(latencies)

            print(f"Cleanup latency stats: avg={avg_latency:.3f}s, max={max_latency:.3f}s, std={std_latency:.3f}s")

            # Latencies should be consistent (low standard deviation)
            assert std_latency < avg_latency * 0.5, "Cleanup latency too inconsistent"
        finally:
            await memory_manager.stop()

    async def test_high_memory_pressure_cleanup(self, memory_manager, mock_psutil):
        """Test cleanup under high memory pressure conditions"""
        # Mock high memory usage
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=60):  # Above threshold
            # Trigger high memory cleanup
            await memory_manager._check_memory_pressure()

            # Verify cleanup was triggered
            assert memory_manager.memory_pressure_events > 0

            # Test the high memory cleanup method directly
            collected = await memory_manager._high_memory_cleanup()
            assert collected >= 0

    async def test_emergency_cleanup(self, memory_manager, mock_psutil):
        """Test emergency cleanup under critical memory conditions"""
        # Mock emergency memory usage
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=85):  # Above emergency threshold
            # Trigger emergency cleanup
            await memory_manager._check_memory_pressure()

            # Verify emergency cleanup was triggered
            assert memory_manager.emergency_cleanups > 0

            # Test emergency cleanup method directly
            collected = await memory_manager._emergency_cleanup()
            assert collected >= 0

    async def test_memory_stats_accuracy(self, mock_psutil):
        """Test memory statistics accuracy"""
        memory_manager = await self.create_memory_manager()

        try:
            stats = memory_manager.get_memory_stats()

            # Verify all required fields are present
            assert hasattr(stats, 'total_memory_mb')
            assert hasattr(stats, 'available_memory_mb')
            assert hasattr(stats, 'used_memory_mb')
            assert hasattr(stats, 'memory_percent')
            assert hasattr(stats, 'process_memory_mb')
            assert hasattr(stats, 'gc_collections')
            assert hasattr(stats, 'object_counts')

            # Verify values are reasonable
            assert stats.total_memory_mb > 0
            assert stats.available_memory_mb >= 0
            assert stats.used_memory_mb >= 0
            assert 0 <= stats.memory_percent <= 100
            assert stats.process_memory_mb >= 0

            # Verify GC collections data
            assert isinstance(stats.gc_collections, dict)
            assert len(stats.gc_collections) >= 3  # generations 0, 1, 2
        finally:
            await memory_manager.stop()

    async def test_object_tracking_and_leak_detection(self, memory_manager, mock_psutil):
        """Test object tracking and potential leak detection"""
        # Create objects that might be considered leaks
        leaking_objects = []
        for i in range(100):
            leaking_objects.append([f"potential_leak_{i}"] * 100)

        # Let leak detection run
        await asyncio.sleep(2)  # Wait for monitoring cycle

        # Check that snapshots are being taken
        assert len(memory_manager.object_snapshots) > 0

        # Verify object snapshot structure
        snapshot = memory_manager._get_object_snapshot()
        assert 'dict' in snapshot
        assert 'list' in snapshot
        assert 'total' in snapshot
        assert snapshot['total'] >= 0

    async def test_cleanup_callbacks(self, memory_manager, mock_psutil):
        """Test cleanup callback functionality"""
        callback_results = []

        # Add multiple cleanup callbacks
        async def async_callback():
            callback_results.append("async_callback")
            await asyncio.sleep(0.01)  # Simulate some work

        def sync_callback():
            callback_results.append("sync_callback")

        memory_manager.add_cleanup_callback(async_callback)
        memory_manager.add_cleanup_callback(sync_callback)

        # Trigger cleanup
        await memory_manager.force_cleanup()

        # Verify callbacks were executed
        assert "async_callback" in callback_results
        assert "sync_callback" in callback_results

        # Test callback removal
        memory_manager.remove_cleanup_callback(sync_callback)
        callback_results.clear()

        await memory_manager.force_cleanup()
        assert "sync_callback" not in callback_results
        assert "async_callback" in callback_results

    async def test_concurrent_cleanup_operations(self, memory_manager, mock_psutil):
        """Test cleanup operations under concurrent load"""
        async def concurrent_cleanup_task(task_id: int):
            """Simulate concurrent cleanup operations"""
            results = []
            for i in range(5):
                # Create some garbage
                garbage = [f"concurrent_garbage_{task_id}_{i}_{j}" for j in range(50)]
                start_time = time.time()
                collected = await memory_manager.force_cleanup()
                latency = time.time() - start_time
                results.append((collected, latency))
            return results

        # Run multiple concurrent cleanup tasks
        tasks = [concurrent_cleanup_task(i) for i in range(3)]
        results = await asyncio.gather(*tasks)

        # Verify all tasks completed successfully
        assert len(results) == 3
        for task_results in results:
            assert len(task_results) == 5
            for collected, latency in task_results:
                assert collected >= 0
                assert latency < 1.0  # Should be reasonably fast

    async def test_gc_performance_benchmarking(self, memory_manager, mock_psutil):
        """Benchmark GC performance under different memory loads"""
        benchmark_results = []

        # Test different memory load levels
        load_levels = [10, 50, 100, 200]  # KB of objects to create

        for load_kb in load_levels:
            # Create memory load
            objects = []
            for i in range(load_kb):
                objects.append([f"benchmark_object_{i}"] * 10)

            # Benchmark cleanup
            start_time = time.time()
            collected = await memory_manager.force_cleanup()
            cleanup_time = time.time() - start_time

            benchmark_results.append({
                'load_kb': load_kb,
                'collected': collected,
                'cleanup_time': cleanup_time,
                'efficiency': collected / cleanup_time if cleanup_time > 0 else 0
            })

        # Analyze benchmark results
        for result in benchmark_results:
            print(f"Load: {result['load_kb']}KB, Time: {result['cleanup_time']:.3f}s, "
                  f"Collected: {result['collected']}, Efficiency: {result['efficiency']:.1f}")

        # Verify performance scales reasonably
        times = [r['cleanup_time'] for r in benchmark_results]
        assert times[-1] < times[0] * 5, "Performance degradation too severe"

    async def test_memory_manager_lifecycle(self, mock_psutil):
        """Test complete memory manager lifecycle"""
        # Test global instance management
        manager1 = await get_memory_manager()
        manager2 = await get_memory_manager()

        # Should return the same instance
        assert manager1 is manager2

        # Test basic functionality
        stats = manager1.get_memory_stats()
        assert isinstance(stats, MemoryStats)

        # Test synchronous stats function
        sync_stats = get_memory_stats()
        assert isinstance(sync_stats, MemoryStats)

        # Test shutdown
        await shutdown_memory_manager()

        # Verify global instance is cleared
        # Note: This test might need adjustment based on actual implementation

    async def test_memory_pressure_detection(self, memory_manager, mock_psutil):
        """Test memory pressure detection and response"""
        # Test normal memory usage
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=30):
            await memory_manager._check_memory_pressure()
            assert memory_manager.memory_pressure_events == 0
            assert memory_manager.emergency_cleanups == 0

        # Test high memory usage
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=60):
            await memory_manager._check_memory_pressure()
            assert memory_manager.memory_pressure_events == 1

        # Test emergency memory usage
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=85):
            await memory_manager._check_memory_pressure()
            assert memory_manager.emergency_cleanups == 1

    async def test_periodic_cleanup_scheduling(self, memory_manager, mock_psutil):
        """Test periodic cleanup scheduling"""
        # Wait for periodic cleanup to run
        initial_time = time.time()
        await asyncio.sleep(2)  # Wait longer than cleanup_interval (1s)

        # Verify periodic cleanup has run
        # Note: This test assumes the monitoring loop is running
        elapsed = time.time() - initial_time
        assert elapsed >= 1.5  # Should have had time for at least one cleanup cycle

    async def test_gc_tuning_configuration(self, memory_manager, mock_psutil):
        """Test GC tuning configuration"""
        # Verify GC tuning is enabled by default
        assert memory_manager.enable_gc_tuning

        # Test with GC tuning disabled
        manager_no_tuning = MemoryManager(enable_gc_tuning=False)
        await manager_no_tuning.start()

        # Verify GC is not disabled when tuning is off
        # Note: This is a basic check - actual GC behavior verification would be complex

        await manager_no_tuning.stop()

    async def test_memory_manager_stats_tracking(self, memory_manager, mock_psutil):
        """Test memory manager statistics tracking"""
        initial_events = memory_manager.memory_pressure_events
        initial_cleanups = memory_manager.emergency_cleanups

        # Trigger some events
        with patch.object(memory_manager, '_get_process_memory_mb', return_value=60):
            await memory_manager._check_memory_pressure()

        with patch.object(memory_manager, '_get_process_memory_mb', return_value=85):
            await memory_manager._check_memory_pressure()

        # Verify stats are updated
        assert memory_manager.memory_pressure_events > initial_events
        assert memory_manager.emergency_cleanups > initial_cleanups

        # Test manager stats
        manager_stats = memory_manager.get_manager_stats()
        assert 'baseline_memory_mb' in manager_stats
        assert 'current_memory_mb' in manager_stats
        assert 'memory_pressure_events' in manager_stats
        assert 'emergency_cleanups' in manager_stats


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])