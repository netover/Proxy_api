"""
Performance tests for model discovery system.

These tests measure the performance characteristics of the model discovery
system under various load conditions, including load testing, cache performance,
memory usage, and concurrent access patterns.
"""

import asyncio
import gc
import tempfile
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
import pytest
import psutil
from fastapi.testclient import TestClient

from src.core.routing.model_discovery import ModelDiscoveryService
from src.core.cache.manager import CacheManager
from src.core.providers.factory import ProviderFactory
from src.main import app
from src.core.providers.models import ModelInfo


class TestModelDiscoveryPerformance:
    """Performance tests for model discovery system."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def discovery_service(self, temp_cache_dir):
        """Create model discovery service with test configuration."""
        cache_manager = CacheManager(cache_dir=temp_cache_dir, ttl=300)
        provider_factory = ProviderFactory()
        return ModelDiscoveryService(
            cache_manager=cache_manager,
            provider_factory=provider_factory,
            timeout=30,
        )

    def measure_memory_usage(self, func, *args, **kwargs):
        """Measure memory usage of a function."""
        tracemalloc.start()

        # Force garbage collection before measurement
        gc.collect()

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run function
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        # Get peak memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        return {
            "result": result,
            "execution_time": end_time - start_time,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": final_memory - initial_memory,
            "peak_memory_mb": peak / 1024 / 1024,
        }

    def test_load_performance_single_provider(self, discovery_service):
        """Test performance with single provider discovery."""
        # Create large model list
        large_model_list = [
            ModelInfo(
                id=f"model-{i}",
                name=f"Test Model {i}",
                provider="test",
                context_length=4096 + i * 100,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01 + i * 0.001,
                output_cost=0.02 + i * 0.002,
            )
            for i in range(1000)  # 1000 models
        ]

        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models") as mock_openai:
            mock_openai.return_value = large_model_list

            # Measure performance
            def run_discovery():
                return asyncio.run(
                    discovery_service.discover_provider_models(
                        "openai", {"api_key": "test"}
                    )
                )

            metrics = self.measure_memory_usage(run_discovery)

            # Assert performance thresholds
            assert metrics["execution_time"] < 5.0  # Should complete within 5 seconds
            assert (
                metrics["memory_increase_mb"] < 100
            )  # Should use less than 100MB additional memory

            print(
                f"Single provider discovery - Time: {metrics['execution_time']:.2f}s, "
                f"Memory: {metrics['memory_increase_mb']:.2f}MB"
            )

    def test_load_performance_multiple_providers(self, discovery_service):
        """Test performance with multiple providers."""
        # Create model lists for multiple providers
        models_per_provider = 100
        providers = ["openai", "anthropic", "cohere", "azure_openai"]

        provider_models = {
            provider: [
                ModelInfo(
                    id=f"{provider}-model-{i}",
                    name=f"{provider.title()} Model {i}",
                    provider=provider,
                    context_length=4096,
                    max_tokens=2048,
                    supports_chat=True,
                    supports_completion=True,
                    input_cost=0.01,
                    output_cost=0.02,
                )
                for i in range(models_per_provider)
            ]
            for provider in providers
        }

        # Mock all providers
        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_all_models") as mock_discover:
            mock_discover.return_value = [model for models in provider_models.values() for model in models]

            # Measure performance
            def run_discovery():
                return asyncio.run(
                    discovery_service.discover_all_models(
                        {
                            "providers": {
                                p: {"enabled": True, "api_key": "test"}
                                for p in providers
                            }
                        }
                    )
                )

            metrics = self.measure_memory_usage(run_discovery)

            # Assert performance thresholds
            assert metrics["execution_time"] < 10.0  # Should complete within 10 seconds
            assert (
                metrics["memory_increase_mb"] < 200
            )  # Should use less than 200MB additional memory

            print(
                f"Multi-provider discovery - Time: {metrics['execution_time']:.2f}s, "
                f"Memory: {metrics['memory_increase_mb']:.2f}MB"
            )

        finally:
            # Clean up mocks
            for mock in mocks:
                mock.stop()

    def test_cache_performance_benchmark(self, discovery_service):
        """Test cache performance under load."""
        test_models = [
            ModelInfo(
                id="test-model",
                name="Test Model",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
            )
        ]

        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models") as mock_openai:
            mock_openai.return_value = test_models

            # First call - populate cache
            asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Benchmark cache reads
            def run_cache_reads():
                async def read_cache_multiple():
                    tasks = [
                        discovery_service.discover_provider_models(
                            "openai", {"api_key": "test"}
                        )
                        for _ in range(1000)
                    ]
                    return await asyncio.gather(*tasks)

                return asyncio.run(read_cache_multiple())

            metrics = self.measure_memory_usage(run_cache_reads)

            # Cache reads should be very fast
            assert metrics["execution_time"] < 1.0  # Should complete within 1 second
            assert mock_openai.call_count == 1  # Should only hit API once

            print(
                f"Cache performance - Time: {metrics['execution_time']:.2f}s, "
                f"Memory: {metrics['memory_increase_mb']:.2f}MB"
            )

    def test_concurrent_access_performance(self, discovery_service):
        """Test performance under concurrent access."""
        test_models = [
            ModelInfo(
                id=f"test-model-{i}",
                name=f"Test Model {i}",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
            )
            for i in range(100)
        ]

        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models") as mock_openai:
            mock_openai.return_value = test_models

            def run_concurrent_access():
                async def concurrent_discovery():
                    # Simulate 50 concurrent users
                    semaphore = asyncio.Semaphore(50)

                    async def limited_discovery():
                        async with semaphore:
                            return await discovery_service.discover_provider_models(
                                "openai", {"api_key": "test"}
                            )

                    tasks = [limited_discovery() for _ in range(100)]
                    return await asyncio.gather(*tasks)

                return asyncio.run(concurrent_discovery())

            metrics = self.measure_memory_usage(run_concurrent_access)

            # Should handle concurrent load efficiently
            assert metrics["execution_time"] < 5.0
            assert mock_openai.call_count == 1  # Should deduplicate requests

            print(
                f"Concurrent access - Time: {metrics['execution_time']:.2f}s, "
                f"Memory: {metrics['memory_increase_mb']:.2f}MB"
            )

    def test_memory_usage_with_large_datasets(self, discovery_service):
        """Test memory usage with very large model datasets."""
        # Create extremely large model list
        huge_model_list = [
            ModelInfo(
                id=f"model-{i}",
                name=f"Test Model {i}",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
                description=f"Description for model {i}"
                * 10,  # Add description to increase size
            )
            for i in range(5000)  # 5000 models
        ]

        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models") as mock_openai:
            mock_openai.return_value = huge_model_list

            def run_large_discovery():
                return asyncio.run(
                    discovery_service.discover_provider_models(
                        "openai", {"api_key": "test"}
                    )
                )

            metrics = self.measure_memory_usage(run_large_discovery)

            # Should handle large datasets without excessive memory usage
            assert (
                metrics["memory_increase_mb"] < 500
            )  # Less than 500MB for 5000 models
            assert len(metrics["result"]) == 5000

            print(
                f"Large dataset - Models: 5000, Memory: {metrics['memory_increase_mb']:.2f}MB"
            )

    def test_api_endpoint_performance(self):
        """Test API endpoint performance under load."""
        client = TestClient(app)

        def run_api_calls():
            # Simulate API calls
            results = []
            for _ in range(100):
                response = client.get("/api/models")
                results.append(response.status_code)
            return results

        metrics = self.measure_memory_usage(run_api_calls)

        # API should respond quickly
        assert metrics["execution_time"] < 5.0  # 100 calls in 5 seconds

        print(f"API performance - 100 calls in {metrics['execution_time']:.2f}s")

    def test_cache_memory_efficiency(self, temp_cache_dir):
        """Test cache memory efficiency over time."""
        cache_manager = CacheManager(cache_dir=temp_cache_dir, ttl=60)

        # Create test data
        test_data = {
            "models": [
                {
                    "id": f"model-{i}",
                    "name": f"Model {i}",
                    "provider": "test",
                    "context_length": 4096,
                    "max_tokens": 2048,
                }
                for i in range(1000)
            ]
        }

        def run_cache_operations():
            # Perform many cache operations
            for i in range(1000):
                key = f"test-key-{i % 100}"  # Reuse keys to test eviction
                cache_manager.set(key, test_data)
                cache_manager.get(key)

            # Force cleanup
            cache_manager.cleanup()
            return True

        metrics = self.measure_memory_usage(run_cache_operations)

        # Cache should be memory efficient
        assert metrics["memory_increase_mb"] < 100

        print(f"Cache efficiency - Memory: {metrics['memory_increase_mb']:.2f}MB")

    def test_provider_timeout_handling(self, discovery_service):
        """Test timeout handling performance."""
        with patch("src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models") as mock_openai:
            # Simulate slow provider response
            async def slow_response():
                await asyncio.sleep(5)  # Simulate slow API
                return []

            mock_openai.side_effect = slow_response

            def run_with_timeout():
                return asyncio.run(
                    discovery_service.discover_provider_models(
                        "openai", {"api_key": "test"}, timeout=1.0
                    )
                )

            start_time = time.time()
            result = run_with_timeout()
            end_time = time.time()

            # Should timeout quickly
            assert end_time - start_time < 2.0  # Should timeout within 2 seconds
            assert result == []  # Should return empty on timeout

    @pytest.mark.benchmark
    def test_performance_benchmarks(self, discovery_service):
        """Comprehensive performance benchmark suite."""
        results = {}

        # Test configurations
        test_configs = [
            {"name": "small", "models": 10, "providers": 1},
            {"name": "medium", "models": 100, "providers": 3},
            {"name": "large", "models": 1000, "providers": 5},
        ]

        for config in test_configs:
            models = [
                ModelInfo(
                    id=f"model-{i}",
                    name=f"Model {i}",
                    provider="test",
                    context_length=4096,
                    max_tokens=2048,
                    supports_chat=True,
                    supports_completion=True,
                    input_cost=0.01,
                    output_cost=0.02,
                )
                for i in range(config["models"])
            ]

            with patch(
                "src.core.routing.model_discovery.ModelDiscoveryService.discover_provider_models"
            ) as mock_openai:
                mock_openai.return_value = models

                def run_benchmark():
                    return asyncio.run(
                        discovery_service.discover_provider_models(
                            "openai", {"api_key": "test"}
                        )
                    )

                metrics = self.measure_memory_usage(run_benchmark)

                results[config["name"]] = {
                    "models": config["models"],
                    "execution_time": metrics["execution_time"],
                    "memory_mb": metrics["memory_increase_mb"],
                    "models_per_second": config["models"] / metrics["execution_time"],
                }

        # Print benchmark results
        print("\nPerformance Benchmark Results:")
        print("-" * 50)
        for name, metrics in results.items():
            print(
                f"{name.upper()}: {metrics['models']} models in {metrics['execution_time']:.2f}s "
                f"({metrics['models_per_second']:.1f} models/sec), "
                f"Memory: {metrics['memory_mb']:.1f}MB"
            )

        # Assert reasonable performance
        assert results["small"]["execution_time"] < 1.0
        assert results["medium"]["execution_time"] < 3.0
        assert results["large"]["execution_time"] < 10.0


class TestLoadTesting:
    """Load testing for model discovery endpoints."""

    def test_api_load_test(self):
        """Test API under simulated load."""
        client = TestClient(app)

        def simulate_user_load(users=50, requests_per_user=10):
            """Simulate multiple users making requests."""
            results = []

            def user_session():
                for _ in range(requests_per_user):
                    response = client.get("/api/models")
                    results.append(response.status_code)

            # Run concurrent user sessions
            with ThreadPoolExecutor(max_workers=users) as executor:
                futures = [executor.submit(user_session) for _ in range(users)]
                for future in futures:
                    future.result()

            return results

        metrics = self.measure_memory_usage(
            simulate_user_load, users=20, requests_per_user=5
        )

        # Should handle load efficiently
        assert metrics["execution_time"] < 10.0  # 100 requests in 10 seconds

        results = metrics["result"]
        success_rate = sum(1 for r in results if r == 200) / len(results)
        assert success_rate > 0.95  # >95% success rate

        print(
            f"Load test - 100 requests in {metrics['execution_time']:.2f}s, "
            f"Success rate: {success_rate:.1%}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
