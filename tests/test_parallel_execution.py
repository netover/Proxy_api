"""
Integration tests for Parallel Execution System
Comprehensive testing of parallel fallback, circuit breaker pool, and load balancer
"""

import asyncio
import time
import pytest
import unittest.mock as mock
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock

from src.core.provider_discovery import provider_discovery, ProviderMetrics
from src.core.parallel_fallback import (
    parallel_fallback_engine,
    ParallelExecutionMode,
)
from src.core.circuit_breaker_pool import (
    circuit_breaker_pool,
    AdaptiveTimeoutConfig,
    TimeoutStrategy,
)
from src.core.load_balancer import load_balancer, LoadBalancingStrategy
from src.core.provider_factory import (
    BaseProvider,
    ProviderStatus,
    provider_factory,
)


class MockProvider(BaseProvider):
    """Mock provider for testing"""

    def __init__(
        self, name: str, response_time: float = 0.1, should_fail: bool = False
    ):
        from src.core.unified_config import ProviderConfig, ProviderType

        config = ProviderConfig(
            name=name,
            type=ProviderType.OPENAI,
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
            models=["gpt-3.5-turbo"],
        )
        super().__init__(config)
        self.response_time = response_time
        self.should_fail = should_fail
        self.call_count = 0

    async def _perform_health_check(self) -> Dict[str, Any]:
        return {"healthy": True, "response_time": 0.05}

    async def create_completion(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.call_count += 1
        if self.should_fail:
            raise Exception("Mock provider failure")

        await asyncio.sleep(self.response_time)
        return {
            "choices": [
                {"message": {"content": f"Response from {self.name}"}}
            ],
            "usage": {"total_tokens": 100},
        }

    async def create_text_completion(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        return await self.create_completion(request)

    async def create_embeddings(
        self, request: Dict[str, Any]
    ) -> Dict[str, Any]:
        self.call_count += 1
        await asyncio.sleep(self.response_time)
        return {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    async def close(self):
        pass


class TestParallelExecutionIntegration:
    """Integration tests for the complete parallel execution system"""

    def setup_method(self):
        """Setup test fixtures"""
        self.providers = {
            "fast_provider": MockProvider("fast_provider", response_time=0.05),
            "medium_provider": MockProvider(
                "medium_provider", response_time=0.15
            ),
            "slow_provider": MockProvider("slow_provider", response_time=0.30),
            "failing_provider": MockProvider(
                "failing_provider", should_fail=True
            ),
        }

        # Mock provider factory
        with mock.patch(
            "src.core.parallel_fallback.provider_factory"
        ) as mock_factory:
            mock_factory.get_provider = AsyncMock(
                side_effect=self._mock_get_provider
            )
            mock_factory.get_all_provider_info = AsyncMock(
                return_value=[
                    type(
                        "ProviderInfo",
                        (),
                        {
                            "name": name,
                            "status": ProviderStatus.HEALTHY,
                            "models": ["gpt-3.5-turbo"],
                        },
                    )()
                    for name in self.providers.keys()
                ]
            )

    def _mock_get_provider(self, name: str):
        return self.providers.get(name)

    @pytest.mark.asyncio
    async def test_first_success_execution(self):
        """Test first-success-wins parallel execution"""
        # Setup provider discovery to return our test providers
        with mock.patch.object(
            provider_discovery,
            "get_healthy_providers_for_model",
            return_value=list(self.providers.keys()),
        ):

            request_data = {"messages": [{"role": "user", "content": "Hello"}]}

            start_time = time.time()
            result = await parallel_fallback_engine.execute_parallel(
                model="gpt-3.5-turbo",
                request_data=request_data,
                execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                timeout=1.0,
                max_providers=3,
            )
            execution_time = time.time() - start_time

            # Should succeed with fast provider
            assert result.success is True
            assert "fast_provider" in result.provider_name
            assert (
                execution_time < 0.2
            )  # Should be much faster than sequential

            # Verify only one provider was actually called (first success)
            called_providers = [
                p for p in self.providers.values() if p.call_count > 0
            ]
            assert len(called_providers) == 1
            assert called_providers[0].name == "fast_provider"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        """Test behavior when all providers fail"""
        failing_providers = {
            "fail1": MockProvider("fail1", should_fail=True),
            "fail2": MockProvider("fail2", should_fail=True),
        }

        with mock.patch(
            "src.core.parallel_fallback.provider_factory"
        ) as mock_factory:
            mock_factory.get_provider = AsyncMock(
                side_effect=lambda name: failing_providers.get(name)
            )
            mock_factory.get_all_provider_info = AsyncMock(
                return_value=[
                    type(
                        "ProviderInfo",
                        (),
                        {
                            "name": name,
                            "status": ProviderStatus.HEALTHY,
                            "models": ["gpt-3.5-turbo"],
                        },
                    )()
                    for name in failing_providers.keys()
                ]
            )

            with mock.patch.object(
                provider_discovery,
                "get_healthy_providers_for_model",
                return_value=list(failing_providers.keys()),
            ):

                request_data = {
                    "messages": [{"role": "user", "content": "Hello"}]
                }

                result = await parallel_fallback_engine.execute_parallel(
                    model="gpt-3.5-turbo",
                    request_data=request_data,
                    execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                    timeout=1.0,
                )

                assert result.success is False
                assert "All providers failed" in result.error
                assert len(result.attempts) == 2  # Both providers attempted

    @pytest.mark.asyncio
    async def test_provider_discovery_health_monitoring(self):
        """Test provider discovery health monitoring"""
        # Reset discovery state
        await provider_discovery.reset_provider_metrics()

        # Record some requests
        await provider_discovery.record_request_result(
            "test_provider", True, 100.0
        )
        await provider_discovery.record_request_result(
            "test_provider", False, 200.0
        )
        await provider_discovery.record_request_result(
            "test_provider", True, 50.0
        )

        metrics = provider_discovery.get_provider_metrics("test_provider")
        assert metrics is not None
        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1

        health = provider_discovery.get_provider_health("test_provider")
        assert (
            health.name == "GOOD"
        )  # Should have good health with 2/3 success rate

    @pytest.mark.asyncio
    async def test_circuit_breaker_pool_adaptive_timeout(self):
        """Test circuit breaker pool with adaptive timeout"""
        # Reset pool
        await circuit_breaker_pool.shutdown()

        provider_name = "test_provider"
        config = AdaptiveTimeoutConfig(
            base_timeout=10.0,
            strategy=TimeoutStrategy.ADAPTIVE,
            adaptation_factor=0.2,
        )

        breaker = await circuit_breaker_pool.get_provider_breaker(
            provider_name, config
        )

        # Simulate some requests with varying latency
        async def mock_request():
            await asyncio.sleep(0.1)  # 100ms response
            return "success"

        # Record several fast requests
        for _ in range(10):
            start_time = time.time()
            await mock_request()
            latency = (time.time() - start_time) * 1000
            await circuit_breaker_pool._record_execution(
                provider_name, True, latency
            )

        # Adapt timeout
        await circuit_breaker_pool.adapt_provider_timeout(provider_name)

        # Timeout should have decreased
        new_timeout = circuit_breaker_pool.get_provider_timeout(provider_name)
        assert new_timeout < 10.0  # Should be less than base timeout

    @pytest.mark.asyncio
    async def test_load_balancer_provider_selection(self):
        """Test load balancer provider selection strategies"""
        # Reset load balancer
        await load_balancer.shutdown()

        providers = ["provider_a", "provider_b", "provider_c"]

        # Test round-robin selection
        selections = []
        for _ in range(6):
            selection = await load_balancer.select_provider(
                "gpt-3.5-turbo", LoadBalancingStrategy.ROUND_ROBIN
            )
            if selection:
                selections.append(selection)

        # Should cycle through providers
        assert len(set(selections)) >= 2  # At least some variety

        # Test least connections
        selection = await load_balancer.select_provider(
            "gpt-3.5-turbo", LoadBalancingStrategy.LEAST_CONNECTIONS
        )
        assert selection in providers

    @pytest.mark.asyncio
    async def test_load_balancer_performance_tracking(self):
        """Test load balancer performance tracking"""
        provider_name = "test_provider"

        # Record request start and completion
        request_id = "test_request_123"
        await load_balancer.record_request_start(provider_name, request_id)

        # Check queue depth
        depth = load_balancer.get_provider_queue_depth(provider_name)
        assert depth == 1

        # Record completion
        await load_balancer.record_request_complete(
            provider_name, request_id, True, 150.0
        )

        # Check queue depth after completion
        depth = load_balancer.get_provider_queue_depth(provider_name)
        assert depth == 0

        # Check load distribution
        distribution = load_balancer.get_load_distribution()
        assert provider_name in distribution
        assert distribution[provider_name]["total_requests"] == 1
        assert distribution[provider_name]["recent_latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_end_to_end_parallel_execution_with_realism(self):
        """Comprehensive end-to-end test with realistic scenarios"""
        # Setup realistic provider mix
        realistic_providers = {
            "openai_fast": MockProvider("openai_fast", response_time=0.2),
            "anthropic_slow": MockProvider(
                "anthropic_slow", response_time=0.8
            ),
            "perplexity_medium": MockProvider(
                "perplexity_medium", response_time=0.4
            ),
        }

        with mock.patch(
            "src.core.parallel_fallback.provider_factory"
        ) as mock_factory:
            mock_factory.get_provider = AsyncMock(
                side_effect=lambda name: realistic_providers.get(name)
            )
            mock_factory.get_all_provider_info = AsyncMock(
                return_value=[
                    type(
                        "ProviderInfo",
                        (),
                        {
                            "name": name,
                            "status": ProviderStatus.HEALTHY,
                            "models": ["gpt-3.5-turbo"],
                        },
                    )()
                    for name in realistic_providers.keys()
                ]
            )

            with mock.patch.object(
                provider_discovery,
                "get_healthy_providers_for_model",
                return_value=list(realistic_providers.keys()),
            ):

                # Test multiple parallel executions
                request_data = {
                    "messages": [{"role": "user", "content": "Test message"}]
                }

                results = []
                for i in range(5):
                    result = await parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                        timeout=2.0,
                        max_providers=3,
                    )
                    results.append(result)

                # All should succeed
                successful_results = [r for r in results if r.success]
                assert len(successful_results) == 5

                # Should use fastest provider (openai_fast)
                winner_providers = [
                    r.provider_name for r in successful_results
                ]
                assert all(
                    "openai_fast" in provider for provider in winner_providers
                )

                # Verify performance improvement
                total_execution_time = (
                    sum(r.latency_ms for r in successful_results) / 1000
                )
                avg_execution_time = total_execution_time / len(
                    successful_results
                )

                # With parallel execution, average should be much better than slowest provider
                assert (
                    avg_execution_time < 1.0
                )  # Much faster than 0.8s slowest provider

    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self):
        """Test that performance metrics are properly collected"""
        # Reset all metrics
        await provider_discovery.reset_provider_metrics()
        await circuit_breaker_pool.shutdown()

        # Execute some requests
        test_providers = ["perf_test_1", "perf_test_2"]

        with mock.patch.object(
            provider_discovery,
            "get_healthy_providers_for_model",
            return_value=test_providers,
        ):
            with mock.patch(
                "src.core.parallel_fallback.provider_factory"
            ) as mock_factory:
                mock_providers = {
                    "perf_test_1": MockProvider(
                        "perf_test_1", response_time=0.1
                    ),
                    "perf_test_2": MockProvider(
                        "perf_test_2", response_time=0.2
                    ),
                }
                mock_factory.get_provider = AsyncMock(
                    side_effect=lambda name: mock_providers.get(name)
                )

                request_data = {
                    "messages": [
                        {"role": "user", "content": "Performance test"}
                    ]
                }

                # Execute parallel requests
                for _ in range(10):
                    await parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        timeout=1.0,
                    )

        # Check metrics
        perf_metrics = parallel_fallback_engine.get_performance_metrics()
        assert perf_metrics["total_executions"] == 10
        assert perf_metrics["successful_executions"] > 0

        # Check provider discovery metrics
        discovery_metrics = provider_discovery.get_all_provider_metrics()
        assert len(discovery_metrics) > 0

        # Check circuit breaker metrics
        breaker_metrics = circuit_breaker_pool.get_pool_metrics()
        assert "providers" in breaker_metrics

    def teardown_method(self):
        """Clean up after tests"""
        # Reset all global instances
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Shutdown all components
            async def cleanup():
                await parallel_fallback_engine.shutdown()
                await load_balancer.shutdown()
                await circuit_breaker_pool.shutdown()
                await provider_discovery.stop_monitoring()

            loop.run_until_complete(cleanup())
        finally:
            loop.close()
