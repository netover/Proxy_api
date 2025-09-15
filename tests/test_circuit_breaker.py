import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
import fakeredis.aioredis

from src.core.circuit_breaker import (
    DistributedCircuitBreaker,
    CircuitBreakerOpenException,
    CircuitState,
    get_circuit_breaker,
)

@pytest.fixture
async def redis_client():
    """Fixture to create a fake redis client for testing."""
    client = fakeredis.aioredis.FakeRedis()
    await client.flushall()
    return client

@pytest.fixture
def circuit_breaker(redis_client):
    """Fixture to create a DistributedCircuitBreaker instance."""
    return DistributedCircuitBreaker(
        redis_client=redis_client,
        service_name="test_service",
        failure_threshold=3,
        recovery_timeout=1,  # 1 second for faster tests
    )

async def successful_func():
    return "success"

async def failing_func():
    raise ValueError("Test failure")

@pytest.mark.asyncio
class TestDistributedCircuitBreaker:
    async def test_initial_state_is_closed(self, circuit_breaker):
        state, failures = await circuit_breaker._get_state()
        assert state == CircuitState.CLOSED
        assert failures == 0

    async def test_successful_execution_remains_closed(self, circuit_breaker):
        result = await circuit_breaker.execute(successful_func)
        assert result == "success"
        state, failures = await circuit_breaker._get_state()
        assert state == CircuitState.CLOSED

    async def test_failures_are_recorded(self, circuit_breaker):
        with pytest.raises(ValueError):
            await circuit_breaker.execute(failing_func)

        state, failures = await circuit_breaker._get_state()
        assert state == CircuitState.CLOSED
        assert failures == 1

    async def test_circuit_opens_after_threshold(self, circuit_breaker):
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        state, failures = await circuit_breaker._get_state()
        assert state == CircuitState.OPEN
        assert failures == 3

    async def test_open_circuit_rejects_requests(self, circuit_breaker):
        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        # Ensure it's open
        state, _ = await circuit_breaker._get_state()
        assert state == CircuitState.OPEN

        # This call should be rejected
        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.execute(successful_func)

    async def test_circuit_transitions_to_half_open(self, circuit_breaker):
        # Trip the circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)

        # Wait for the recovery timeout
        await asyncio.sleep(1.1)

        # The state should now be half-open
        state, _ = await circuit_breaker._get_state()
        assert state == CircuitState.HALF_OPEN

    async def test_half_open_closes_on_success(self, circuit_breaker):
        # Trip the circuit and wait for half-open state
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)
        await asyncio.sleep(1.1)

        # A successful call in half-open state should close the circuit
        result = await circuit_breaker.execute(successful_func)
        assert result == "success"

        state, failures = await circuit_breaker._get_state()
        assert state == CircuitState.CLOSED
        assert failures == 0

    async def test_half_open_reopens_on_failure(self, circuit_breaker):
        # Trip the circuit and wait for half-open state
        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.execute(failing_func)
        await asyncio.sleep(1.1)

        # A failing call in half-open state should re-open the circuit
        with pytest.raises(ValueError):
            await circuit_breaker.execute(failing_func)

        state, _ = await circuit_breaker._get_state()
        assert state == CircuitState.OPEN

@patch('src.core.circuit_breaker.get_redis_client')
def test_get_circuit_breaker_factory(mock_get_redis_client):
    """Test the get_circuit_breaker factory function."""
    # Mock the redis client factory to avoid real connections
    mock_get_redis_client.return_value = fakeredis.FakeRedis()

    # Mock config manager
    with patch('src.core.circuit_breaker.config_manager') as mock_config_manager:
        mock_config = MagicMock()
        mock_config.settings.circuit_breaker_threshold = 5
        mock_config.settings.circuit_breaker_timeout = 60
        mock_config_manager.load_config.return_value = mock_config

        cb1 = get_circuit_breaker("factory_test_1")
        cb2 = get_circuit_breaker("factory_test_2")
        cb3 = get_circuit_breaker("factory_test_1")  # Should return the same instance

        assert isinstance(cb1, DistributedCircuitBreaker)
        assert cb1 is cb3
        assert cb1 is not cb2
