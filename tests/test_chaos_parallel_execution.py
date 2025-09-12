"""
Chaos Engineering Tests for Parallel Execution System
Testing failure scenarios and system resilience
"""

import asyncio
import time
import pytest
import random
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from src.core.parallel_fallback import parallel_fallback_engine, ParallelExecutionMode
from src.core.provider_discovery import provider_discovery
from src.core.circuit_breaker_pool import circuit_breaker_pool
from src.core.load_balancer import load_balancer


class ChaoticProvider:
    """Provider that exhibits chaotic behavior for testing"""

    def __init__(self, name: str, failure_rate: float = 0.0, latency_variation: float = 0.0):
        self.name = name
        self.failure_rate = failure_rate
        self.base_latency = 0.1
        self.latency_variation = latency_variation
        self.call_count = 0

    async def execute_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        self.call_count += 1

        # Simulate random failures
        if random.random() < self.failure_rate:
            await asyncio.sleep(random.uniform(0.01, 0.1))  # Brief delay before failure
            raise Exception(f"Chaotic failure in {self.name}")

        # Simulate variable latency
        latency = self.base_latency + random.uniform(-self.latency_variation, self.latency_variation)
        latency = max(0.01, latency)  # Minimum 10ms
        await asyncio.sleep(latency)

        return {
            "choices": [{"message": {"content": f"Response from {self.name} (attempt {self.call_count})"}}],
            "usage": {"total_tokens": 100}
        }


class TestChaosEngineering:
    """Chaos engineering tests for parallel execution resilience"""

    @pytest.mark.asyncio
    async def test_high_failure_rate_resilience(self):
        """Test system resilience with high provider failure rates"""
        providers = {
            "reliable": ChaoticProvider("reliable", failure_rate=0.05),     # 5% failure
            "unreliable": ChaoticProvider("unreliable", failure_rate=0.80), # 80% failure
            "very_unreliable": ChaoticProvider("very_unreliable", failure_rate=0.95) # 95% failure
        }

        with self._mock_provider_factory(providers):
            with self._mock_provider_discovery(list(providers.keys())):

                request_data = {"messages": [{"role": "user", "content": "Chaos test"}]}

                results = []
                for i in range(20):  # Test many requests
                    result = await parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                        timeout=2.0,
                        max_providers=3
                    )
                    results.append(result)

                # Analyze results
                successful_results = [r for r in results if r.success]
                success_rate = len(successful_results) / len(results)

                # Should maintain reasonable success rate despite chaos
                assert success_rate > 0.7  # At least 70% success rate

                # Check that all providers were attempted
                provider_calls = {name: provider.call_count for name, provider in providers.items()}
                assert all(calls > 0 for calls in provider_calls.values())

    @pytest.mark.asyncio
    async def test_network_partition_simulation(self):
        """Test behavior during simulated network partitions"""
        providers = {
            "provider_a": ChaoticProvider("provider_a", failure_rate=0.0),
            "provider_b": ChaoticProvider("provider_b", failure_rate=0.0),
            "provider_c": ChaoticProvider("provider_c", failure_rate=1.0),  # Always fails
        }

        # Simulate network partition affecting provider_c
        original_execute = providers["provider_c"].execute_request
        async def partitioned_execute(request_data):
            # Simulate network timeout
            await asyncio.sleep(5.0)  # Longer than our timeout
            raise Exception("Network partition")

        providers["provider_c"].execute_request = partitioned_execute

        with self._mock_provider_factory(providers):
            with self._mock_provider_discovery(list(providers.keys())):

                request_data = {"messages": [{"role": "user", "content": "Partition test"}]}

                start_time = time.time()
                result = await parallel_fallback_engine.execute_parallel(
                    model="gpt-3.5-turbo",
                    request_data=request_data,
                    execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                    timeout=1.0,  # Short timeout
                    max_providers=3
                )
                execution_time = time.time() - start_time

                # Should succeed despite partition
                assert result.success is True

                # Should complete quickly (not wait for partitioned provider)
                assert execution_time < 1.5

                # Should use one of the healthy providers
                assert result.provider_name in ["provider_a", "provider_b"]

    @pytest.mark.asyncio
    async def test_cascading_failure_protection(self):
        """Test protection against cascading failures"""
        providers = {
            "primary": ChaoticProvider("primary", failure_rate=0.0),
            "secondary": ChaoticProvider("secondary", failure_rate=0.0),
        }

        # Simulate cascading failure - secondary fails after primary starts failing
        failure_count = 0
        original_primary_execute = providers["primary"].execute_request

        async def cascading_failure(request_data):
            nonlocal failure_count
            failure_count += 1
            if failure_count > 3:  # Start failing after a few successes
                raise Exception("Cascading failure in primary")
            return await original_primary_execute(request_data)

        providers["primary"].execute_request = cascading_failure

        with self._mock_provider_factory(providers):
            with self._mock_provider_discovery(list(providers.keys())):

                request_data = {"messages": [{"role": "user", "content": "Cascading test"}]}

                results = []
                for i in range(10):
                    result = await parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                        timeout=2.0
                    )
                    results.append(result)

                # Should eventually failover to secondary
                successful_results = [r for r in results if r.success]
                assert len(successful_results) > 5  # Most should succeed

                # Should use both providers
                used_providers = set(r.provider_name for r in successful_results)
                assert len(used_providers) >= 1

    @pytest.mark.asyncio
    async def test_load_shedding_under_high_load(self):
        """Test load shedding behavior under extreme load"""
        providers = {
            "fast": ChaoticProvider("fast", failure_rate=0.0, latency_variation=0.05),
            "medium": ChaoticProvider("medium", failure_rate=0.0, latency_variation=0.1),
            "slow": ChaoticProvider("slow", failure_rate=0.0, latency_variation=0.2),
        }

        with self._mock_provider_factory(providers):
            with self._mock_provider_discovery(list(providers.keys())):

                request_data = {"messages": [{"role": "user", "content": "Load test"}]}

                # Simulate high concurrent load
                tasks = []
                for i in range(50):  # High concurrency
                    task = asyncio.create_task(
                        parallel_fallback_engine.execute_parallel(
                            model="gpt-3.5-turbo",
                            request_data=request_data,
                            execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                            timeout=3.0
                        )
                    )
                    tasks.append(task)

                # Wait for all to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Analyze results
                successful_results = [r for r in results if isinstance(r, dict) and r.get('success')]
                failed_results = [r for r in results if isinstance(r, dict) and not r.get('success')]

                success_rate = len(successful_results) / len(results)
                assert success_rate > 0.8  # Should maintain high success rate under load

                # Check load distribution
                provider_usage = {}
                for result in successful_results:
                    provider = result.get('provider_name')
                    provider_usage[provider] = provider_usage.get(provider, 0) + 1

                # Should distribute load across providers
                assert len(provider_usage) >= 2  # Should use multiple providers

    @pytest.mark.asyncio
    async def test_adaptive_timeout_under_varying_conditions(self):
        """Test adaptive timeout behavior under varying network conditions"""
        provider_name = "adaptive_test"

        # Start with stable conditions
        await circuit_breaker_pool.reset_provider_breaker(provider_name)

        # Simulate varying latency conditions
        latency_scenarios = [
            0.1, 0.1, 0.1,  # Stable fast
            0.5, 0.5, 0.5,  # Slow down
            2.0, 2.0,        # Very slow
            0.1, 0.1, 0.1,  # Speed up again
        ]

        for latency in latency_scenarios:
            # Record request with current latency
            await circuit_breaker_pool._record_execution(provider_name, True, latency * 1000)

            # Adapt timeout
            await circuit_breaker_pool.adapt_provider_timeout(provider_name)

        # Check that timeout has adapted
        final_timeout = circuit_breaker_pool.get_provider_timeout(provider_name)

        # Should be different from base timeout due to adaptation
        assert final_timeout != 30.0  # Base timeout

        # Should be reasonable (not too extreme)
        assert 5.0 <= final_timeout <= 120.0

    @pytest.mark.asyncio
    async def test_provider_discovery_under_failure_storm(self):
        """Test provider discovery during failure storm"""
        providers = ["storm_test_1", "storm_test_2", "storm_test_3"]

        # Reset metrics
        await provider_discovery.reset_provider_metrics()

        # Simulate failure storm
        for i in range(100):
            for provider in providers:
                success = random.random() > 0.7  # 70% success rate
                latency = random.uniform(0.1, 2.0) * 1000  # 100ms to 2s
                await provider_discovery.record_request_result(provider, success, latency)

        # Check health assessment
        for provider in providers:
            health = provider_discovery.get_provider_health(provider)
            metrics = provider_discovery.get_provider_metrics(provider)

            # Should have collected metrics
            assert metrics.total_requests >= 90  # Roughly 100 requests per provider
            assert metrics.error_rate < 0.5  # Should detect the failure pattern

        # Should still be able to select healthy providers
        healthy_providers = provider_discovery.get_healthy_providers_for_model("gpt-3.5-turbo")
        assert len(healthy_providers) >= 1  # At least one should be considered healthy

    def _mock_provider_factory(self, providers):
        """Helper to mock provider factory"""
        from unittest.mock import patch
        return patch('src.core.parallel_fallback.provider_factory')

    def _mock_provider_discovery(self, provider_names):
        """Helper to mock provider discovery"""
        from unittest.mock import patch
        return patch.object(
            provider_discovery,
            'get_healthy_providers_for_model',
            return_value=provider_names
        )

    def teardown_method(self):
        """Clean up after chaos tests"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            async def cleanup():
                await parallel_fallback_engine.shutdown()
                await circuit_breaker_pool.shutdown()
                await provider_discovery.stop_monitoring()
                await load_balancer.shutdown()

            loop.run_until_complete(cleanup())
        finally:
            loop.close()