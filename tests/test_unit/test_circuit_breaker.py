"""
Unit tests for circuit breaker implementation.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.core.breaker.circuit_breaker import CircuitBreaker, CircuitBreakerState, get_circuit_breaker, _circuit_breakers


@pytest.fixture(autouse=True)
def clear_circuit_breakers():
    """Clear circuit breaker registry before each test."""
    _circuit_breakers.clear()


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(
            name="test_breaker",
            failure_threshold=3,
            recovery_timeout=30,
            half_open_max_calls=5
        )

        assert breaker.name == "test_breaker"
        assert breaker.failure_threshold == 3
        assert breaker.recovery_timeout == 30
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_successful_calls(self):
        """Test successful circuit breaker calls."""
        breaker = CircuitBreaker("test", failure_threshold=3)

        # Mock successful function
        async def success_func():
            return "success"

        # Should allow calls when closed
        for i in range(5):
            result = await breaker.call(success_func)
            assert result == "success"

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.success_count == 5
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_threshold(self):
        """Test circuit breaker failure threshold."""
        breaker = CircuitBreaker("test", failure_threshold=2)

        # Mock failing function
        async def failing_func():
            raise Exception("Service unavailable")

        # First failure
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.state == CircuitBreakerState.CLOSED
        assert breaker.failure_count == 1

        # Second failure should open circuit
        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.state == CircuitBreakerState.OPEN
        assert breaker.failure_count == 2

    @pytest.mark.asyncio
    async def test_circuit_open_rejection(self):
        """Test that open circuit rejects calls."""
        breaker = CircuitBreaker("test", failure_threshold=1)

        # Fail once to open circuit
        async def failing_func():
            raise Exception("Service error")

        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.state == CircuitBreakerState.OPEN

        # Subsequent calls should be rejected immediately
        with pytest.raises(Exception):  # Should raise CircuitBreakerOpenError
            await breaker.call(lambda: "success")

    @pytest.mark.asyncio
    async def test_half_open_transition(self):
        """Test half-open state transition."""
        breaker = CircuitBreaker(
            "test",
            failure_threshold=1,
            recovery_timeout=1  # Short timeout for testing
        )

        # Open the circuit
        async def failing_func():
            raise Exception("Service error")

        with pytest.raises(Exception):
            await breaker.call(failing_func)

        assert breaker.state == CircuitBreakerState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next call should transition to half-open
        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self):
        """Test circuit breaker metrics collection."""
        breaker = CircuitBreaker("test", failure_threshold=2)

        # Mock some calls
        async def success_func():
            return "success"

        async def failing_func():
            raise Exception("Error")

        # Mix of successes and failures
        await breaker.call(success_func)  # Success
        with pytest.raises(Exception):
            await breaker.call(failing_func)  # Failure

        await breaker.call(success_func)  # Success
        with pytest.raises(Exception):
            await breaker.call(failing_func)  # Failure (opens circuit)

        # Check metrics
        assert breaker.success_count == 2
        assert breaker.failure_count == 2
        assert breaker.total_calls == 4


class TestCircuitBreakerPool:
    """Test circuit breaker pool functionality."""

    @pytest.mark.asyncio
    async def test_global_circuit_breaker_access(self):
        """Test accessing circuit breakers globally."""
        # Get breaker for a provider
        breaker = get_circuit_breaker("test_provider")

        assert breaker is not None
        assert breaker.name == "test_provider"

        # Should return the same instance
        breaker2 = get_circuit_breaker("test_provider")
        assert breaker is breaker2

    @pytest.mark.asyncio
    async def test_multiple_providers(self):
        """Test circuit breakers for multiple providers."""
        breaker1 = get_circuit_breaker("provider1")
        breaker2 = get_circuit_breaker("provider2")

        assert breaker1.name == "provider1"
        assert breaker2.name == "provider2"
        assert breaker1 is not breaker2

    @pytest.mark.asyncio
    async def test_circuit_breaker_state_isolation(self):
        """Test that circuit breaker states are isolated."""
        breaker1 = get_circuit_breaker("provider1", failure_threshold=2)  # Lower threshold for testing
        breaker2 = get_circuit_breaker("provider2")

        # Fail provider1 twice to reach threshold (default is 5, but let's make it 1 for testing)
        async def failing_func():
            raise Exception("Error")

        # First failure
        with pytest.raises(Exception):
            await breaker1.call(failing_func)

        # Second failure should open the circuit
        with pytest.raises(Exception):
            await breaker1.call(failing_func)

        assert breaker1.state == CircuitBreakerState.OPEN
        assert breaker2.state == CircuitBreakerState.CLOSED  # Should be unaffected


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration with HTTP client."""

    @pytest.mark.asyncio
    async def test_http_client_with_circuit_breaker(self):
        """Test HTTP client integration with circuit breaker."""
        from src.core.http.client_v2 import OptimizedHTTPClient

        # Create client with circuit breaker
        breaker = get_circuit_breaker("test_provider")
        client = OptimizedHTTPClient(circuit_breaker=breaker)

        # Initialize the client
        await client.initialize()

        # Mock successful response
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.status_code = 200

        async def mock_request(**kwargs):
            return mock_response

        with patch.object(client._client, 'request', side_effect=mock_request):
            response = await client.request("GET", "http://example.com")

            assert response.status_code == 200

        await client.close()
