"""
Tests for circuit breaker implementation
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from src.core.circuit_breaker import (
    CircuitBreaker, 
    CircuitState, 
    CircuitBreakerOpenException,
    get_circuit_breaker,
    get_all_circuit_breakers
)

class TestCircuitBreaker:
    """Test circuit breaker functionality"""

    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker for testing"""
        return CircuitBreaker(
            name="test_cb",
            failure_threshold=3,
            recovery_timeout=1  # 1 second for faster tests
        )

    @pytest.mark.asyncio
    async def test_initial_state(self, circuit_breaker):
        """Test initial circuit breaker state"""
        assert circuit_breaker.is_closed()
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None

    @pytest.mark.asyncio
    async def test_successful_execution(self, circuit_breaker):
        """Test successful function execution"""
        async def successful_func():
            return "success"

        result = await circuit_breaker.execute(successful_func)
        assert result == "success"
        assert circuit_breaker.is_closed()
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_failure_handling(self, circuit_breaker):
        """Test failure handling"""
        async def failing_func():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception, match="Test failure"):
            await circuit_breaker.execute(failing_func)
        
        assert circuit_breaker.is_closed()
        assert circuit_breaker.failure_count == 1

        # Second failure
        with pytest.raises(Exception, match="Test failure"):
            await circuit_breaker.execute(failing_func)
        
        assert circuit_breaker.is_closed()
        assert circuit_breaker.failure_count == 2

        # Third failure (should trip circuit)
        with pytest.raises(Exception, match="Test failure"):
            await circuit_breaker.execute(failing_func)
        
        assert circuit_breaker.is_open()
        assert circuit_breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_open_rejection(self, circuit_breaker):
        """Test that open circuit rejects requests"""
        # Trip the circuit
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time()

        async def any_func():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.execute(any_func)

    @pytest.mark.asyncio
    async def test_half_open_state(self, circuit_breaker):
        """Test half-open state behavior"""
        # Set circuit to open state
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time() - 2  # Past recovery timeout

        # Should move to half-open on can_execute check
        can_execute = await circuit_breaker.can_execute()
        assert can_execute
        assert circuit_breaker.is_half_open()

    @pytest.mark.asyncio
    async def test_half_open_success_recovery(self, circuit_breaker):
        """Test recovery from half-open state on success"""
        # Set circuit to half-open state
        circuit_breaker.state = CircuitState.HALF_OPEN

        async def successful_func():
            return "recovered"

        result = await circuit_breaker.execute(successful_func)
        assert result == "recovered"
        assert circuit_breaker.is_closed()
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopen(self, circuit_breaker):
        """Test reopening circuit from half-open state on failure"""
        # Set circuit to half-open state
        circuit_breaker.state = CircuitState.HALF_OPEN

        async def failing_func():
            raise Exception("Half-open failure")

        with pytest.raises(Exception, match="Half-open failure"):
            await circuit_breaker.execute(failing_func)
        
        # After failure in half-open state, circuit should go back to OPEN
        # but failure count should reset to 1 (not increment from previous state)
        assert circuit_breaker.is_open()
        assert circuit_breaker.failure_count == 1


    @pytest.mark.asyncio
    async def test_recovery_timeout(self, circuit_breaker):
        """Test recovery timeout behavior"""
        # Trip the circuit
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time() - 2  # Past recovery timeout

        async def test_func():
            return "should work"

        # Should be able to execute after recovery timeout
        result = await circuit_breaker.execute(test_func)
        assert result == "should work"

    def test_get_circuit_breaker(self):
        """Test circuit breaker registry"""
        cb1 = get_circuit_breaker("test_registry_1")
        cb2 = get_circuit_breaker("test_registry_2")
        cb3 = get_circuit_breaker("test_registry_1")  # Should return same instance

        assert cb1 is cb3  # Same instance
        assert cb1 is not cb2  # Different instances

        all_cbs = get_all_circuit_breakers()
        assert "test_registry_1" in all_cbs
        assert "test_registry_2" in all_cbs
        assert all_cbs["test_registry_1"] is cb1
        assert all_cbs["test_registry_2"] is cb2
