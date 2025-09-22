"""
Tests for the robust, distributed Circuit Breaker implementation.
Verifies atomic state transitions using a mocked Redis client.
"""

import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis  # Import the top-level redis package for exceptions
import redis.asyncio as aioredis
from src.core.breaker.circuit_breaker import (
    CircuitBreakerOpenException,
    CircuitState,
    DistributedCircuitBreaker,
    InMemoryCircuitBreaker,  # Import for the test
    get_circuit_breaker,
    initialize_circuit_breakers,
)

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_redis():
    """Fixture to create a mock of the redis.asyncio.Redis client."""
    mock_redis_client = AsyncMock(spec=aioredis.Redis)

    # The pipeline object that redis_client.pipeline() will return
    pipeline_mock = AsyncMock()

    # When the pipeline is used as a context manager, __aenter__ should return
    # an object that has the methods we need (get, set, watch, etc.)
    pipeline_mock.__aenter__.return_value = pipeline_mock

    # Configure the methods on the pipeline object
    pipeline_mock.get = AsyncMock()
    pipeline_mock.set = AsyncMock()
    pipeline_mock.watch = AsyncMock()
    pipeline_mock.multi = MagicMock()  # multi is not async
    pipeline_mock.execute = AsyncMock()

    mock_redis_client.pipeline.return_value = pipeline_mock

    # Also mock the top-level methods for non-pipeline operations
    mock_redis_client.get = AsyncMock(return_value=None)
    mock_redis_client.set = AsyncMock()
    mock_redis_client.delete = AsyncMock()
    mock_redis_client.ping = AsyncMock()  # For initialization test

    return mock_redis_client


@pytest.fixture
def circuit_breaker(mock_redis):
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


@pytest.mark.asyncio
class TestDistributedCircuitBreaker:
    async def test_initial_state_is_closed(self, circuit_breaker, mock_redis):
        state = await circuit_breaker._get_state()
        assert state["state"] == CircuitState.CLOSED.value
        assert state["failures"] == 0
        mock_redis.get.assert_called_once_with(circuit_breaker.key)

    @pytest.mark.asyncio
    async def test_successful_call_in_closed_state(self, circuit_breaker, mock_redis):
        result = await circuit_breaker.call(successful_func)
        assert result == "success"
        # No change to state, so no set/delete calls
        mock_redis.set.assert_not_called()
        mock_redis.delete.assert_not_called()

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    @patch("random.random", return_value=0.5)
    async def test_recovery_timeout_with_jitter(self, mock_random, mock_redis):
        """Test that jitter is added to the recovery timeout."""
        breaker = DistributedCircuitBreaker(
            redis_client=mock_redis,
            service_name="test_jitter",
            recovery_timeout=10
        )
        # Set state to OPEN
        open_state = json.dumps(
            {
                "state": CircuitState.OPEN.value,
                "failures": 3,
                "timestamp": time.time(),
            }
        )
        mock_redis.get.return_value = open_state

        # Wait for less than the full timeout + jitter
        await asyncio.sleep(10)
        state = await breaker._get_state()
        assert state["state"] == CircuitState.OPEN.value

        # Wait for the full timeout + jitter
        await asyncio.sleep(1)
        state = await breaker._get_state()
        assert state["state"] == CircuitState.HALF_OPEN.value

    @pytest.mark.asyncio
    async def test_open_circuit_rejects_calls(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    async def test_circuit_moves_to_half_open(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    async def test_half_open_closes_on_success(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    async def test_half_open_reopens_on_failure(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    async def test_transaction_retry_on_watch_error(self, circuit_breaker, mock_redis):
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

    @pytest.mark.asyncio
    async def test_redis_connection_error_fallback(self, mock_redis):
        """Test that the circuit breaker falls back to in-memory state when Redis is down."""
        # Configure the mock to raise ConnectionError
        mock_redis.get.side_effect = redis.ConnectionError
        mock_redis.set.side_effect = redis.ConnectionError
        mock_redis.delete.side_effect = redis.ConnectionError
        pipeline = mock_redis.pipeline.return_value
        pipeline.execute.side_effect = redis.ConnectionError
        pipeline.get.return_value = None # Ensure the pipeline's get returns a valid value

        breaker = DistributedCircuitBreaker(
            redis_client=mock_redis,
            service_name="test_fallback",
            failure_threshold=3
        )

        # First call should be allowed (in-memory state is CLOSED)
        state = await breaker._get_state()
        assert state["state"] == "CLOSED"

        # Record failures until the breaker opens
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)

        # The in-memory state should now be OPEN
        assert breaker.in_memory_state["state"] == "OPEN"
        assert breaker.in_memory_state["failures"] == 3

        # Further calls should be blocked
        with pytest.raises(CircuitBreakerOpenException):
            await breaker.call(successful_func)


class TestCircuitBreakerFactory:
    async def test_get_circuit_breaker(self, mock_redis):
        """Test the get_circuit_breaker factory function."""
        await initialize_circuit_breakers(mock_redis)

        cb1 = get_circuit_breaker("factory_test_1")
        cb2 = get_circuit_breaker("factory_test_2")
        cb3 = get_circuit_breaker("factory_test_1")  # Should return the same instance

        assert isinstance(cb1, DistributedCircuitBreaker)
        assert cb1 is cb3
        assert cb1 is not cb2
        assert cb1.redis is mock_redis

    async def test_fallback_to_in_memory_breaker(self):
        """Test that get_circuit_breaker falls back to InMemoryCircuitBreaker if not initialized."""
        # Reset the global state for this test
        from src.core.breaker import circuit_breaker

        circuit_breaker._redis_client = None
        circuit_breaker._circuit_breakers = {}

        # Should not raise an error, but create an in-memory breaker
        with patch.object(circuit_breaker.logger, "warning") as mock_warning:
            breaker = get_circuit_breaker("in_memory_test")
            assert isinstance(breaker, InMemoryCircuitBreaker)
            mock_warning.assert_called_once_with(
                "Creating in-memory circuit breaker for 'in_memory_test'."
            )
