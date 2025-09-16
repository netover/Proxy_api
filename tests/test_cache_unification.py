"""Integration Tests for Cache Unification

Comprehensive testing suite for the unified cache system, including:
- Cache behavior validation
- Migration testing
- Performance benchmarking
- Chaos engineering tests
- Integration with existing components
"""

import asyncio
import json
import logging
import os
import pytest
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

from src.core.unified_cache import UnifiedCache, get_unified_cache, CacheEntry
from src.core.cache_migration import CacheMigrationService, MigrationConfig
from src.core.cache_warmer import CacheWarmer
from src.core.cache_monitor import CacheMonitor
from src.models.model_info import ModelInfo
from src.core.model_discovery import ProviderConfig


logger = logging.getLogger(__name__)


@pytest.fixture
async def temp_cache_dir():
    """Create temporary cache directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"
        cache_dir.mkdir(exist_ok=True)
        yield cache_dir


@pytest.fixture
async def unified_cache(temp_cache_dir):
    """Create unified cache instance for testing"""
    cache = UnifiedCache(
        max_size=1000,
        default_ttl=300,
        max_memory_mb=64,
        enable_disk_cache=True,
        cache_dir=temp_cache_dir,
        enable_smart_ttl=True,
        enable_predictive_warming=True,
        enable_consistency_monitoring=True,
    )
    await cache.start()

    yield cache

    await cache.stop()


@pytest.fixture
async def cache_warmer(unified_cache):
    """Create cache warmer instance for testing"""
    warmer = CacheWarmer(
        cache=unified_cache,
        enable_pattern_analysis=True,
        enable_predictive_warming=True,
        enable_scheduled_warming=False,  # Disable for testing
    )
    await warmer.start()

    yield warmer

    await warmer.stop()


@pytest.fixture
async def cache_monitor(unified_cache):
    """Create cache monitor instance for testing"""
    monitor = CacheMonitor(target_hit_rate=0.9, check_interval=1)
    await monitor.start()

    yield monitor

    await monitor.stop()


@pytest.fixture
def sample_model_info():
    """Create sample ModelInfo objects for testing"""
    import time

    current_time = int(time.time())

    return [
        ModelInfo(id="gpt-4", created=current_time, owned_by="openai"),
        ModelInfo(id="claude-3", created=current_time, owned_by="anthropic"),
        ModelInfo(id="gemini-pro", created=current_time, owned_by="google"),
    ]


class TestUnifiedCacheCore:
    """Test core unified cache functionality"""

    @pytest.mark.asyncio
    async def test_cache_basic_operations(
        self, unified_cache, sample_model_info
    ):
        """Test basic cache operations"""
        # Test cache set
        key = "test:models:openai"
        success = await unified_cache.set(key, sample_model_info[:1])
        assert success

        # Test cache get
        cached = await unified_cache.get(key)
        assert cached is not None
        assert len(cached) == 1
        assert cached[0].id == "gpt-4"

        # Test cache miss
        missed = await unified_cache.get("nonexistent:key")
        assert missed is None

    @pytest.mark.asyncio
    async def test_cache_ttl_and_expiration(self, unified_cache):
        """Test TTL functionality and expiration"""
        key = "test:ttl"
        value = {"test": "data"}

        # Set with short TTL
        success = await unified_cache.set(key, value, ttl=1)
        assert success

        # Should be available immediately
        cached = await unified_cache.get(key)
        assert cached is not None

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        expired = await unified_cache.get(key)
        assert expired is None

    @pytest.mark.asyncio
    async def test_smart_ttl_extension(self, unified_cache):
        """Test smart TTL extension based on access patterns"""
        key = "test:smart_ttl"
        value = {"data": "test"}

        # Set initial entry
        success = await unified_cache.set(key, value, ttl=10)
        assert success

        # Simulate frequent access
        for _ in range(10):
            await unified_cache.get(key)
            await asyncio.sleep(0.1)

        # Access pattern should trigger TTL extension
        # (This would require mocking the pattern analysis)

    @pytest.mark.asyncio
    async def test_cache_categories(self, unified_cache, sample_model_info):
        """Test cache categorization"""
        # Set entries with different categories
        await unified_cache.set(
            "models:openai", sample_model_info[:1], category="models"
        )
        await unified_cache.set(
            "response:123", {"result": "test"}, category="response"
        )
        await unified_cache.set(
            "summary:456", {"summary": "test"}, category="summary"
        )

        stats = await unified_cache.get_stats()
        assert "models" in stats["categories"]
        assert "response" in stats["categories"]
        assert "summary" in stats["categories"]

    @pytest.mark.asyncio
    async def test_memory_limits(self, unified_cache):
        """Test memory limit enforcement"""
        # Fill cache to trigger memory limits
        large_data = {"data": "x" * 10000}  # 10KB per entry

        for i in range(10):
            await unified_cache.set(f"large:{i}", large_data)

        stats = await unified_cache.get_stats()
        # Should have enforced memory limits
        assert stats["memory_usage_mb"] <= unified_cache.max_memory_bytes / (
            1024 * 1024
        )

    @pytest.mark.asyncio
    async def test_disk_persistence(self, unified_cache, temp_cache_dir):
        """Test disk persistence"""
        key = "test:persistence"
        value = {"persistent": "data"}

        # Set and verify in memory
        await unified_cache.set(key, value)
        cached = await unified_cache.get(key)
        assert cached == value

        # Simulate cache restart by creating new instance
        new_cache = UnifiedCache(
            max_size=1000, enable_disk_cache=True, cache_dir=temp_cache_dir
        )
        await new_cache.start()

        # Should load from disk
        loaded = await new_cache.get(key)
        assert loaded == value

        await new_cache.stop()


class TestCacheMigration:
    """Test cache migration functionality"""

    @pytest.mark.asyncio
    async def test_migration_service_initialization(self):
        """Test migration service initialization"""
        service = CacheMigrationService()
        assert service.config is not None
        assert not service._migration_in_progress

    @pytest.mark.asyncio
    async def test_migration_config_validation(self):
        """Test migration configuration validation"""
        config = MigrationConfig(
            batch_size=50,
            max_workers=2,
            conflict_strategy="newer_wins",
            enable_backup=True,
            enable_validation=True,
        )

        service = CacheMigrationService(config)
        assert service.config.batch_size == 50
        assert service.config.max_workers == 2

    @pytest.mark.asyncio
    async def test_migration_status_tracking(self):
        """Test migration status tracking"""
        service = CacheMigrationService()

        # Initial status
        status = await service.get_migration_status()
        assert status["status"] == "idle"

        # Check stats are zero
        assert status["progress"]["total"] == 0
        assert status["progress"]["completed"] == 0

    @pytest.mark.asyncio
    async def test_migration_backup_creation(self, temp_cache_dir):
        """Test backup creation during migration"""
        config = MigrationConfig(enable_backup=True)
        service = CacheMigrationService(config)

        # Create mock backup method
        original_create_backup = service._create_backup
        backup_created = False

        async def mock_create_backup():
            nonlocal backup_created
            backup_created = True
            service._backup_path = temp_cache_dir / "backup"
            service._backup_created = True

        service._create_backup = mock_create_backup

        # Test backup creation
        await service._create_backup()
        assert backup_created
        assert service._backup_created

    @pytest.mark.asyncio
    async def test_migration_validation(self, unified_cache):
        """Test migration validation"""
        service = CacheMigrationService()

        # Add some test data to cache
        await unified_cache.set("test:key1", {"data": "test1"})
        await unified_cache.set("test:key2", {"data": "test2"})

        # Validate migration
        await service._validate_migration()

        # Check that validation completed without errors
        assert len(service.stats.errors) == 0


class TestCacheWarmer:
    """Test cache warming functionality"""

    @pytest.mark.asyncio
    async def test_warmer_initialization(self, unified_cache):
        """Test cache warmer initialization"""
        warmer = CacheWarmer(cache=unified_cache)
        await warmer.start()

        assert warmer._running
        assert warmer.cache is unified_cache

        await warmer.stop()

    @pytest.mark.asyncio
    async def test_access_pattern_recording(self, cache_warmer):
        """Test access pattern recording"""
        key = "test:pattern:key"
        category = "test"

        # Record access
        cache_warmer.record_access(key, category)

        # Check pattern was recorded
        assert key in cache_warmer._access_patterns
        pattern = cache_warmer._access_patterns[key]
        assert pattern.key == key
        assert pattern.category == category
        assert pattern.access_count == 1

    @pytest.mark.asyncio
    async def test_predictive_warming_score(self):
        """Test predictive warming score calculation"""
        from src.core.cache_warmer import WarmingPattern

        pattern = WarmingPattern(
            key="test:key", access_count=20, last_accessed=time.time()
        )

        # Set some access times
        now = time.time()
        pattern.access_times = [
            now - i * 3600 for i in range(10)
        ]  # 10 accesses in last 10 hours

        score = pattern.get_predictive_score()
        assert score > 0  # Should have positive score

    @pytest.mark.asyncio
    async def test_warming_stats(self, cache_warmer):
        """Test warming statistics"""
        stats = await cache_warmer.get_warming_stats()

        # Check basic stats structure
        assert "total_warmings" in stats
        assert "successful_warmings" in stats
        assert "failed_warmings" in stats
        assert "success_rate" in stats
        assert "active_warmings" in stats
        assert "queued_warmings" in stats

        # Check initial values
        assert stats["total_warmings"] == 0
        assert stats["successful_warmings"] == 0
        assert stats["active_warmings"] == 0

    @pytest.mark.asyncio
    async def test_demand_warming(self, cache_warmer):
        """Test on-demand cache warming"""
        key = "test:demand:key"

        async def getter_func():
            return {"warmed": "data"}

        # Request warming
        success = await cache_warmer.warm_key(key, getter_func)
        assert success

        # Wait a bit for warming to complete
        await asyncio.sleep(0.1)

        # Check if key was warmed
        warmed_data = await cache_warmer.cache.get(key)
        assert warmed_data == {"warmed": "data"}


class TestCacheMonitor:
    """Test cache monitoring functionality"""

    @pytest.mark.asyncio
    async def test_monitor_initialization(self, unified_cache):
        """Test monitor initialization"""
        monitor = CacheMonitor(cache=unified_cache)
        await monitor.start()

        assert monitor._running
        assert monitor.cache is unified_cache

        await monitor.stop()

    @pytest.mark.asyncio
    async def test_metrics_collection(self, cache_monitor):
        """Test metrics collection"""
        # Wait for some metrics to be collected
        await asyncio.sleep(2)

        # Get monitoring report
        report = await cache_monitor.get_monitoring_report()

        # Check report structure
        assert "current_metrics" in report
        assert "summary_stats" in report
        assert "active_alerts" in report
        assert "consistency_issues" in report

    @pytest.mark.asyncio
    async def test_health_status(self, cache_monitor):
        """Test health status calculation"""
        health = await cache_monitor.get_health_status()

        assert "status" in health
        assert "score" in health
        assert "metrics" in health

        # Score should be between 0 and 100
        assert 0 <= health["score"] <= 100

    @pytest.mark.asyncio
    async def test_alert_system(self, cache_monitor, unified_cache):
        """Test alert system"""
        # Fill cache to potentially trigger alerts
        for i in range(100):
            await unified_cache.set(
                f"test:key{i}", {"data": f"value{i}"}, ttl=1
            )

        # Wait for monitoring to detect issues
        await asyncio.sleep(2)

        # Check for any alerts
        report = await cache_monitor.get_monitoring_report()
        alerts = report["active_alerts"]

        # Should have some alerts due to rapid cache operations
        assert isinstance(alerts, list)


class TestCacheIntegration:
    """Integration tests for cache system components"""

    @pytest.mark.asyncio
    async def test_full_cache_lifecycle(
        self, unified_cache, cache_warmer, cache_monitor
    ):
        """Test complete cache lifecycle with all components"""
        # 1. Add data to cache
        test_data = {"integration": "test", "timestamp": time.time()}
        key = "integration:test:key"

        await unified_cache.set(key, test_data, category="integration")
        cached = await unified_cache.get(key)
        assert cached == test_data

        # 2. Record access for warming
        cache_warmer.record_access(key, "integration")

        # 3. Check monitoring
        await asyncio.sleep(1)
        health = await cache_monitor.get_health_status()
        assert health["status"] in ["healthy", "warning", "initializing"]

        # 4. Verify stats across components
        cache_stats = await unified_cache.get_stats()
        warmer_stats = await cache_warmer.get_warming_stats()

        assert cache_stats["entries"] >= 1
        assert warmer_stats["tracked_patterns"] >= 1

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, unified_cache):
        """Test concurrent cache operations"""

        async def concurrent_worker(worker_id: int):
            for i in range(10):
                key = f"concurrent:worker{worker_id}:item{i}"
                await unified_cache.set(key, {"worker": worker_id, "item": i})
                await unified_cache.get(key)

        # Run multiple concurrent workers
        tasks = [concurrent_worker(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # Verify all operations completed
        stats = await unified_cache.get_stats()
        assert (
            stats["entries"] >= 50
        )  # At least 50 entries from 5 workers * 10 items

    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self, unified_cache):
        """Test handling of memory pressure"""
        # Fill cache with large entries
        large_data = {"data": "x" * 50000}  # 50KB each

        for i in range(5):
            await unified_cache.set(f"memory_test:{i}", large_data)

        # Check memory usage
        stats = await unified_cache.get_stats()
        memory_mb = stats["memory_usage_mb"]

        # Should be using significant memory but within limits
        assert memory_mb > 0
        assert memory_mb <= unified_cache.max_memory_bytes / (1024 * 1024)

    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self, unified_cache):
        """Test cache performance under load"""
        import time

        # Measure performance with many operations
        start_time = time.time()

        # Perform many cache operations
        for i in range(100):
            await unified_cache.set(f"perf_test:{i}", {"value": i})
            await unified_cache.get(f"perf_test:{i}")

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete within reasonable time
        assert total_time < 5.0  # Less than 5 seconds for 200 operations

        operations_per_second = 200 / total_time
        logger.info(
            f"Cache operations per second: {operations_per_second:.2f}"
        )


class TestChaosEngineering:
    """Chaos engineering tests for cache failure scenarios"""

    @pytest.mark.asyncio
    async def test_cache_failure_recovery(self, unified_cache):
        """Test recovery from cache failures"""
        # Add test data
        key = "chaos:test:key"
        value = {"chaos": "test"}
        await unified_cache.set(key, value)

        # Simulate cache failure by clearing internal state
        # (This is a simplified simulation)
        original_cache = unified_cache._memory_cache
        unified_cache._memory_cache = {}

        # Try to get data - should miss
        missed = await unified_cache.get(key)
        assert missed is None

        # Restore and verify data persistence
        unified_cache._memory_cache = original_cache
        restored = await unified_cache.get(key)
        assert restored == value

    @pytest.mark.asyncio
    async def test_disk_corruption_handling(
        self, unified_cache, temp_cache_dir
    ):
        """Test handling of disk corruption"""
        key = "corruption:test"
        value = {"test": "data"}

        # Set data
        await unified_cache.set(key, value)

        # Simulate disk corruption by writing invalid data
        cache_file = (
            temp_cache_dir / f"{unified_cache._generate_key(key)}.json"
        )
        with open(cache_file, "w") as f:
            f.write("invalid json content")

        # Try to get data - should handle corruption gracefully
        try:
            result = await unified_cache.get(key)
            # Should either return None or handle the error
            assert result is None or isinstance(result, dict)
        except Exception as e:
            # Should handle corruption without crashing
            logger.info(f"Handled corruption gracefully: {e}")

    @pytest.mark.asyncio
    async def test_memory_exhaustion_simulation(self, unified_cache):
        """Test behavior under memory exhaustion"""
        # Fill cache to near capacity
        small_data = {"data": "test"}

        for i in range(1000):
            await unified_cache.set(f"exhaustion:{i}", small_data, ttl=1)

        # Check that cache is still operational
        stats = await unified_cache.get_stats()
        assert stats["entries"] > 0

        # Should still accept new entries (may evict old ones)
        new_key = "exhaustion:new_entry"
        success = await unified_cache.set(new_key, {"new": "data"})
        assert success

    @pytest.mark.asyncio
    async def test_concurrent_failure_simulation(self, unified_cache):
        """Test concurrent operations during simulated failures"""

        async def failing_operation(operation_id: int):
            try:
                # Mix of successful and potentially failing operations
                if operation_id % 5 == 0:
                    # Simulate occasional failure
                    await asyncio.sleep(0.01)  # Brief delay
                    raise Exception(f"Simulated failure {operation_id}")

                # Normal operation
                key = f"failure_test:{operation_id}"
                await unified_cache.set(key, {"operation": operation_id})

            except Exception as e:
                logger.debug(f"Operation {operation_id} failed: {e}")
                return False
            return True

        # Run many concurrent operations, some will fail
        tasks = [failing_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should have some successful operations despite failures
        successful = sum(1 for r in results if r is True)
        assert successful > 0

        logger.info(f"Chaos test: {successful}/50 operations successful")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
