"""
Tests for the robust, distributed Circuit Breaker implementation.
Verifies atomic state transitions using a mocked Redis client.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.core.circuit_breaker import (
    CircuitBreakerOpenException,
    CircuitState,
    DistributedCircuitBreaker,
    get_circuit_breaker,
    initialize_circuit_breakers,
)

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis():
    """Fixture to create a mock of the redis.asyncio.Redis client."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()

    # Mock the pipeline for transactions
    pipeline = AsyncMock()
    pipeline.get = mock.get
    pipeline.set = mock.set
    pipeline.multi = MagicMock()
    pipeline.execute = AsyncMock()
    pipeline.watch = AsyncMock()

    mock.pipeline.return_value = pipeline
    return mock


@pytest.fixture
async def circuit_breaker(mock_redis):
    """Fixture to create a DistributedCircuitBreaker instance with a mocked redis."""
    breaker = DistributedCircuitBreaker(
        redis_client=mock_redis,
        service_name="test_service",
        failure_threshold=3,
        recovery_timeout=1,  # 1 second for faster tests
    )
    return breaker


async def successful_func():
    """A function that always succeeds."""
    return "success"


async def failing_func():
    """A function that always fails."""
    raise ValueError("Test failure")


class TestDistributedCircuitBreaker:
    async def test_initial_state_is_closed(self, circuit_breaker, mock_redis):
        state = await circuit_breaker._get_state()
        assert state["state"] == CircuitState.CLOSED.value
        assert state["failures"] == 0
        mock_redis.get.assert_called_once_with(circuit_breaker.key)

    async def test_successful_call_in_closed_state(
        self, circuit_breaker, mock_redis
    ):
        result = await circuit_breaker.call(successful_func)
        assert result == "success"
        # No change to state, so no set/delete calls
        mock_redis.set.assert_not_called()
        mock_redis.delete.assert_not_called()

    async def test_failure_increments_count(self, circuit_breaker, mock_redis):
        # Mock the pipeline to control the transaction
        pipeline = mock_redis.pipeline.return_value
        pipeline.get.return_value = None  # First call, no state exists

        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        # Verify that the failure was recorded with a transaction
        pipeline.watch.assert_called_once_with(circuit_breaker.key)
        pipeline.multi.assert_called_once()
        pipeline.execute.assert_called_once()

        # Check the new state that was set
        expected_state = {
            "state": CircuitState.CLOSED.value,
            "failures": 1,
            "timestamp": time.time(),
        }
        # Get the call arguments for the set call
        call_args = pipeline.set.call_args[0]
        actual_state = json.loads(call_args[1])

        assert call_args[0] == circuit_breaker.key
        assert actual_state["state"] == expected_state["state"]
        assert actual_state["failures"] == expected_state["failures"]

    async def test_circuit_opens_after_threshold(
        self, circuit_breaker, mock_redis
    ):
        # Simulate 2 existing failures
        initial_state = json.dumps(
            {
                "state": CircuitState.CLOSED.value,
                "failures": 2,
                "timestamp": time.time(),
            }
        )
        pipeline = mock_redis.pipeline.return_value
        pipeline.get.return_value = initial_state

        # The 3rd failure should open the circuit
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        # Verify it set the state to OPEN
        call_args = pipeline.set.call_args[0]
        actual_state = json.loads(call_args[1])
        assert actual_state["state"] == CircuitState.OPEN.value
        assert actual_state["failures"] == 3

    async def test_open_circuit_rejects_calls(
        self, circuit_breaker, mock_redis
    ):
        # Set state to OPEN
        open_state = json.dumps(
            {
                "state": CircuitState.OPEN.value,
                "failures": 3,
                "timestamp": time.time(),
            }
        )
        mock_redis.get.return_value = open_state

        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.call(successful_func)

    async def test_circuit_moves_to_half_open(
        self, circuit_breaker, mock_redis
    ):
        # Set state to OPEN, but with an expired timestamp
        expired_time = time.time() - circuit_breaker.recovery_timeout - 1
        open_state = json.dumps(
            {
                "state": CircuitState.OPEN.value,
                "failures": 3,
                "timestamp": expired_time,
            }
        )
        mock_redis.get.return_value = open_state

        # Getting the state should trigger the move to HALF_OPEN
        state = await circuit_breaker._get_state()
        assert state["state"] == CircuitState.HALF_OPEN.value

        # Verify that the new HALF_OPEN state was written to Redis
        call_args = mock_redis.set.call_args[0]
        actual_state = json.loads(call_args[1])
        assert actual_state["state"] == CircuitState.HALF_OPEN.value

    async def test_half_open_closes_on_success(
        self, circuit_breaker, mock_redis
    ):
        # Set state to HALF_OPEN
        half_open_state = json.dumps(
            {
                "state": CircuitState.HALF_OPEN.value,
                "failures": 0,
                "timestamp": time.time(),
            }
        )
        mock_redis.get.return_value = half_open_state

        # A successful call should reset the circuit
        await circuit_breaker.call(successful_func)

        # Verify the key was deleted (resetting to CLOSED)
        mock_redis.delete.assert_called_once_with(circuit_breaker.key)

    async def test_half_open_reopens_on_failure(
        self, circuit_breaker, mock_redis
    ):
        # Set state to HALF_OPEN
        half_open_state = json.dumps(
            {
                "state": CircuitState.HALF_OPEN.value,
                "failures": 0,
                "timestamp": time.time(),
            }
        )
        mock_redis.get.return_value = half_open_state

        pipeline = mock_redis.pipeline.return_value
        pipeline.get.return_value = half_open_state

        # A failing call should move it back to OPEN
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        # Verify it set the state back to OPEN
        call_args = pipeline.set.call_args[0]
        actual_state = json.loads(call_args[1])
        assert actual_state["state"] == CircuitState.OPEN.value

    async def test_transaction_retry_on_watch_error(
        self, circuit_breaker, mock_redis
    ):
        """Test that the failure recording logic retries if a WatchError occurs."""
        pipeline = mock_redis.pipeline.return_value

        # Simulate a WatchError on the first attempt, then succeed
        pipeline.execute.side_effect = [redis.WatchError, AsyncMock()]

        # The first GET in the transaction returns no state
        # The second GET (after WatchError) also returns no state
        pipeline.get.side_effect = [None, None]

        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        # The pipeline should have been executed twice
        assert pipeline.execute.call_count == 2
        # Watch should have been called twice
        assert pipeline.watch.call_count == 2


class TestCircuitBreakerFactory:
    async def test_get_circuit_breaker(self):
        """Test the get_circuit_breaker factory function."""
        mock_redis_client = AsyncMock()
        await initialize_circuit_breakers(mock_redis_client)

        cb1 = get_circuit_breaker("factory_test_1")
        cb2 = get_circuit_breaker("factory_test_2")
        cb3 = get_circuit_breaker(
            "factory_test_1"
        )  # Should return the same instance

        assert isinstance(cb1, DistributedCircuitBreaker)
        assert cb1 is cb3
        assert cb1 is not cb2
        assert cb1.redis is mock_redis_client

    async def test_get_breaker_before_init_raises_error(self):
        """Test that calling get_circuit_breaker before initialization raises an error."""
        # Reset the global state for this test
        from src.core import circuit_breaker

        circuit_breaker._redis_client = None
        circuit_breaker._circuit_breakers = {}

        with pytest.raises(RuntimeError):
            get_circuit_breaker("uninitialized_test")
