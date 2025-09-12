"""
Tests for circuit breaker implementation
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.circuit_breaker import (
    CircuitBreaker,
    ProductionCircuitBreaker,
    CircuitState,
    CircuitBreakerOpenException,
    get_circuit_breaker,
    get_all_circuit_breakers,
    get_circuit_breaker_metrics,
    reset_all_circuit_breakers
)
from src.core.circuit_breaker_pool import (
    CircuitBreakerPool,
    AdaptiveTimeoutConfig,
    TimeoutStrategy,
    ProviderCircuitBreaker
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
        # Trip the circuit by setting state on the internal breaker
        circuit_breaker._breaker.state = CircuitState.OPEN
        circuit_breaker._breaker.last_failure_time = time.time()

        async def any_func():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenException):
            await circuit_breaker.execute(any_func)

    @pytest.mark.asyncio
    async def test_half_open_state(self, circuit_breaker):
        """Test half-open state behavior"""
        # Set circuit to open state
        circuit_breaker._breaker.state = CircuitState.OPEN
        circuit_breaker._breaker.last_failure_time = time.time() - 2  # Past recovery timeout

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
        circuit_breaker._breaker.state = CircuitState.HALF_OPEN

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
        circuit_breaker._breaker.state = CircuitState.OPEN
        circuit_breaker._breaker.last_failure_time = time.time() - 2  # Past recovery timeout

        async def test_func():
            return "should work"

        # Should be able to execute after recovery timeout
        result = await circuit_breaker.execute(test_func)
        assert result == "should work"

    @patch('src.core.circuit_breaker.config_manager')
    def test_get_circuit_breaker(self, mock_config_manager):
        """Test circuit breaker registry"""
        # Mock the config manager to avoid loading real config
        mock_config = MagicMock()
        mock_config.settings.circuit_breaker_threshold = 5
        mock_config.settings.circuit_breaker_timeout = 60
        mock_config_manager.load_config.return_value = mock_config

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


class TestProductionCircuitBreaker:
    """Test ProductionCircuitBreaker with advanced features"""

    @pytest.fixture
    def prod_circuit_breaker(self):
        """Create a production circuit breaker for testing"""
        return ProductionCircuitBreaker(
            name="test_prod_cb",
            failure_threshold=5,
            recovery_timeout=2,
            success_threshold=3,
            min_failure_threshold=2,
            max_failure_threshold=15,
            adaptive_thresholds=True
        )

    @pytest.mark.asyncio
    async def test_adaptive_threshold_high_success_rate(self, prod_circuit_breaker):
        """Test adaptive threshold reduction with high success rate"""
        # Simulate high success rate (95%+)
        for i in range(20):
            if i < 19:  # 19 successes out of 20
                await prod_circuit_breaker.on_success()
            else:
                await prod_circuit_breaker.on_failure(Exception("Test failure"))

        # Threshold should decrease
        assert prod_circuit_breaker.failure_threshold < 5

    @pytest.mark.asyncio
    async def test_adaptive_threshold_low_success_rate(self, prod_circuit_breaker):
        """Test adaptive threshold increase with low success rate"""
        # Simulate low success rate (<80%)
        for i in range(10):
            if i < 2:  # Only 2 successes out of 10
                await prod_circuit_breaker.on_success()
            else:
                await prod_circuit_breaker.on_failure(Exception("Test failure"))

        # Threshold should increase
        assert prod_circuit_breaker.failure_threshold > 5

    @pytest.mark.asyncio
    async def test_adaptive_threshold_bounds(self, prod_circuit_breaker):
        """Test that adaptive thresholds respect min/max bounds"""
        # Force very low success rate to test upper bound
        for i in range(50):
            await prod_circuit_breaker.on_failure(Exception("Test failure"))

        assert prod_circuit_breaker.failure_threshold <= prod_circuit_breaker.max_failure_threshold

        # Reset and test lower bound
        prod_circuit_breaker.failure_threshold = 5
        for i in range(50):
            await prod_circuit_breaker.on_success()

        assert prod_circuit_breaker.failure_threshold >= prod_circuit_breaker.min_failure_threshold

    @pytest.mark.asyncio
    async def test_success_rate_calculation(self, prod_circuit_breaker):
        """Test success rate calculation with EMA"""
        # Initial success rate should be None or 1.0
        assert prod_circuit_breaker.get_success_rate() == 1.0

        # Add some successes and failures
        await prod_circuit_breaker.on_success()
        await prod_circuit_breaker.on_success()
        await prod_circuit_breaker.on_failure(Exception("Test"))
        await prod_circuit_breaker.on_success()

        success_rate = prod_circuit_breaker.get_success_rate()
        assert 0.0 <= success_rate <= 1.0

    @pytest.mark.asyncio
    async def test_half_open_success_threshold(self, prod_circuit_breaker):
        """Test half-open state requires multiple successes to close"""
        # Set to half-open state
        prod_circuit_breaker.state = CircuitState.HALF_OPEN

        # First success
        await prod_circuit_breaker.on_success()
        assert prod_circuit_breaker.is_half_open()
        assert prod_circuit_breaker.half_open_success_count == 1

        # Second success
        await prod_circuit_breaker.on_success()
        assert prod_circuit_breaker.is_half_open()
        assert prod_circuit_breaker.half_open_success_count == 2

        # Third success should close the circuit
        await prod_circuit_breaker.on_success()
        assert prod_circuit_breaker.is_closed()
        assert prod_circuit_breaker.half_open_success_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_immediate_trip(self, prod_circuit_breaker):
        """Test that any failure in half-open state immediately trips circuit"""
        # Set to half-open state
        prod_circuit_breaker.state = CircuitState.HALF_OPEN

        # Any failure should immediately trip to OPEN
        await prod_circuit_breaker.on_failure(Exception("Half-open failure"))
        assert prod_circuit_breaker.is_open()
        assert prod_circuit_breaker.half_open_success_count == 0
        assert prod_circuit_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_recovery_timeout_with_half_open_transition(self, prod_circuit_breaker):
        """Test recovery timeout leads to half-open state"""
        # Trip the circuit
        for _ in range(6):
            await prod_circuit_breaker.on_failure(Exception("Test"))

        assert prod_circuit_breaker.is_open()

        # Simulate time passing beyond recovery timeout
        prod_circuit_breaker.last_failure_time = time.time() - 3  # Past 2 second timeout

        # Next can_execute should transition to half-open
        can_execute = await prod_circuit_breaker.can_execute()
        assert can_execute
        assert prod_circuit_breaker.is_half_open()

    @pytest.mark.asyncio
    async def test_metrics_comprehensive_tracking(self, prod_circuit_breaker):
        """Test comprehensive metrics tracking"""
        initial_metrics = prod_circuit_breaker.get_metrics()

        # Perform various operations
        await prod_circuit_breaker.on_success()
        await prod_circuit_breaker.on_failure(Exception("Test"))
        await prod_circuit_breaker.on_success()

        # Trip and recover
        for _ in range(6):
            await prod_circuit_breaker.on_failure(Exception("Test"))

        updated_metrics = prod_circuit_breaker.get_metrics()

        # Verify metrics are updated
        assert updated_metrics['total_requests'] > initial_metrics['total_requests']
        assert updated_metrics['successful_requests'] > initial_metrics['successful_requests']
        assert updated_metrics['failed_requests'] > initial_metrics['failed_requests']
        assert updated_metrics['state_changes'] >= initial_metrics['state_changes']

    @pytest.mark.asyncio
    async def test_concurrent_access_thread_safety(self, prod_circuit_breaker):
        """Test thread safety with concurrent operations"""
        async def concurrent_operation(operation_type: str):
            if operation_type == "success":
                await prod_circuit_breaker.on_success()
            else:
                await prod_circuit_breaker.on_failure(Exception("Concurrent test"))

        # Run multiple concurrent operations
        tasks = []
        for i in range(10):
            tasks.append(asyncio.create_task(
                concurrent_operation("success" if i % 2 == 0 else "failure")
            ))

        await asyncio.gather(*tasks)

        # Verify final state is consistent
        metrics = prod_circuit_breaker.get_metrics()
        assert metrics['total_requests'] == 10
        assert metrics['successful_requests'] + metrics['failed_requests'] == 10


class TestCircuitBreakerRecovery:
    """Test circuit breaker recovery mechanisms and simulation"""

    @pytest.fixture
    def recovery_breaker(self):
        """Create circuit breaker optimized for recovery testing"""
        return ProductionCircuitBreaker(
            name="recovery_test",
            failure_threshold=3,
            recovery_timeout=1,  # Fast recovery for testing
            success_threshold=2,
            adaptive_thresholds=True
        )

    @pytest.mark.asyncio
    async def test_automatic_recovery_after_timeout(self, recovery_breaker):
        """Test automatic transition to half-open after recovery timeout"""
        # Trip the circuit
        for _ in range(4):
            await recovery_breaker.on_failure(Exception("Trip circuit"))

        assert recovery_breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Next request should transition to half-open
        can_execute = await recovery_breaker.can_execute()
        assert can_execute
        assert recovery_breaker.is_half_open()

    @pytest.mark.asyncio
    async def test_successful_recovery_sequence(self, recovery_breaker):
        """Test complete recovery sequence: OPEN -> HALF_OPEN -> CLOSED"""
        # Trip circuit
        for _ in range(4):
            await recovery_breaker.on_failure(Exception("Initial failure"))

        assert recovery_breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # First request in half-open should succeed
        async def success_func():
            return "success"

        result = await recovery_breaker.execute(success_func)
        assert result == "success"
        assert recovery_breaker.is_half_open()

        # Second success should close circuit
        result2 = await recovery_breaker.execute(success_func)
        assert result2 == "success"
        assert recovery_breaker.is_closed()

    @pytest.mark.asyncio
    async def test_failed_recovery_attempt(self, recovery_breaker):
        """Test failed recovery attempt returns to OPEN state"""
        # Trip circuit
        for _ in range(4):
            await recovery_breaker.on_failure(Exception("Initial failure"))

        assert recovery_breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # First request succeeds, second fails
        async def success_func():
            return "success"

        async def failure_func():
            raise Exception("Recovery failure")

        result = await recovery_breaker.execute(success_func)
        assert result == "success"
        assert recovery_breaker.is_half_open()

        # Failure in half-open should return to OPEN
        with pytest.raises(Exception, match="Recovery failure"):
            await recovery_breaker.execute(failure_func)

        assert recovery_breaker.is_open()

    @pytest.mark.asyncio
    async def test_recovery_with_adaptive_thresholds(self, recovery_breaker):
        """Test recovery behavior with adaptive thresholds"""
        # Start with high failure threshold due to good performance
        for _ in range(20):
            await recovery_breaker.on_success()

        initial_threshold = recovery_breaker.failure_threshold
        assert initial_threshold < 3  # Should be reduced

        # Trip circuit
        for _ in range(initial_threshold + 1):
            await recovery_breaker.on_failure(Exception("Trip with adaptive threshold"))

        assert recovery_breaker.is_open()

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Successful recovery should maintain or improve threshold
        for _ in range(3):
            async def success_func():
                return "success"
            await recovery_breaker.execute(success_func)

        assert recovery_breaker.is_closed()
        # Threshold should be at or below initial (good performance)
        assert recovery_breaker.failure_threshold <= initial_threshold

    @pytest.mark.asyncio
    async def test_recovery_timeout_calculation(self, recovery_breaker):
        """Test recovery timeout calculation and retry-after header"""
        # Trip circuit
        for _ in range(4):
            await recovery_breaker.on_failure(Exception("Trip"))

        assert recovery_breaker.is_open()

        # Test retry-after calculation
        async def test_func():
            return "should fail"

        with pytest.raises(CircuitBreakerOpenException) as exc_info:
            await recovery_breaker.execute(test_func)

        # Should have retry_after information
        assert exc_info.value.retry_after is not None
        assert exc_info.value.retry_after > 0

    @pytest.mark.asyncio
    async def test_downtime_calculation_during_recovery(self, recovery_breaker):
        """Test downtime calculation during recovery process"""
        initial_metrics = recovery_breaker.get_metrics()
        initial_downtime = initial_metrics['total_downtime_seconds']

        # Trip circuit
        trip_time = time.time()
        for _ in range(4):
            await recovery_breaker.on_failure(Exception("Trip"))

        assert recovery_breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Recover successfully
        async def success_func():
            return "success"

        await recovery_breaker.execute(success_func)
        await recovery_breaker.execute(success_func)

        final_metrics = recovery_breaker.get_metrics()

        # Downtime should be calculated
        assert final_metrics['total_downtime_seconds'] > initial_downtime
        # Should be approximately the recovery timeout
        downtime_increase = final_metrics['total_downtime_seconds'] - initial_downtime
        assert 1.0 <= downtime_increase <= 2.0  # Allow some margin

    @pytest.mark.asyncio
    async def test_multiple_recovery_cycles(self, recovery_breaker):
        """Test multiple recovery cycles with different patterns"""
        recovery_count = 0

        for cycle in range(3):
            # Trip circuit
            for _ in range(4):
                await recovery_breaker.on_failure(Exception(f"Cycle {cycle} failure"))

            assert recovery_breaker.is_open()

            # Wait for recovery
            await asyncio.sleep(1.1)

            # Recovery attempt
            if cycle < 2:  # First two cycles succeed
                async def success_func():
                    return "success"
                await recovery_breaker.execute(success_func)
                await recovery_breaker.execute(success_func)
                assert recovery_breaker.is_closed()
                recovery_count += 1
            else:  # Third cycle fails
                async def failure_func():
                    raise Exception("Final failure")
                with pytest.raises(Exception):
                    await recovery_breaker.execute(failure_func)
                assert recovery_breaker.is_open()

        assert recovery_count == 2
        metrics = recovery_breaker.get_metrics()
        assert metrics['state_changes'] >= 6  # OPEN->HALF_OPEN->CLOSED cycles


class TestFailureScenarios:
    """Test circuit breaker behavior under various failure scenarios"""

    @pytest.fixture
    def failure_breaker(self):
        """Create circuit breaker for failure scenario testing"""
        return ProductionCircuitBreaker(
            name="failure_scenario_test",
            failure_threshold=3,
            recovery_timeout=1,
            adaptive_thresholds=True
        )

    @pytest.mark.asyncio
    async def test_intermittent_failures(self, failure_breaker):
        """Test behavior with intermittent failure patterns"""
        pattern = [True, False, True, False, True, False, False, False]  # Mixed success/failure

        for i, should_succeed in enumerate(pattern):
            if should_succeed:
                await failure_breaker.on_success()
            else:
                await failure_breaker.on_failure(Exception(f"Intermittent failure {i}"))

        # Should not trip due to intermittent nature
        assert failure_breaker.is_closed()
        assert failure_breaker.failure_count < failure_breaker.failure_threshold

    @pytest.mark.asyncio
    async def test_burst_failures(self, failure_breaker):
        """Test behavior with burst failure patterns"""
        # Initial successes
        for _ in range(5):
            await failure_breaker.on_success()

        # Burst of failures
        for _ in range(4):
            await failure_breaker.on_failure(Exception("Burst failure"))

        # Should trip
        assert failure_breaker.is_open()

        # Recovery attempt
        await asyncio.sleep(1.1)
        async def recovery_func():
            return "recovered"

        result = await failure_breaker.execute(recovery_func)
        assert result == "recovered"
        assert failure_breaker.is_half_open()

    @pytest.mark.asyncio
    async def test_gradual_failure_increase(self, failure_breaker):
        """Test gradual increase in failure rate"""
        # Start with mostly successes
        for i in range(10):
            if i < 8:
                await failure_breaker.on_success()
            else:
                await failure_breaker.on_failure(Exception("Gradual failure"))

        assert failure_breaker.is_closed()

        # Increase failure rate
        for i in range(8):
            if i < 3:
                await failure_breaker.on_success()
            else:
                await failure_breaker.on_failure(Exception("Increased failure"))

        # Should eventually trip
        assert failure_breaker.is_open()

    @pytest.mark.asyncio
    async def test_different_exception_types(self, failure_breaker):
        """Test circuit breaker with different exception types"""
        exceptions = [
            ValueError("Value error"),
            ConnectionError("Connection failed"),
            TimeoutError("Timeout"),
            RuntimeError("Runtime error"),
            Exception("Generic exception")
        ]

        for exc in exceptions:
            await failure_breaker.on_failure(exc)

        # Should trip regardless of exception type
        assert failure_breaker.is_open()

    @pytest.mark.asyncio
    async def test_expected_vs_unexpected_exceptions(self, failure_breaker):
        """Test handling of expected vs unexpected exceptions"""
        # Test with expected exceptions
        expected_exceptions = (ValueError, ConnectionError, TimeoutError)

        breaker_with_expected = ProductionCircuitBreaker(
            name="expected_test",
            failure_threshold=3,
            expected_exceptions=expected_exceptions
        )

        # Expected exception should be handled
        await breaker_with_expected.on_failure(ValueError("Expected"))
        assert breaker_with_expected.failure_count == 1

        # Unexpected exception should also be handled (Exception is in expected)
        await breaker_with_expected.on_failure(RuntimeError("Unexpected but still handled"))
        assert breaker_with_expected.failure_count == 2

    @pytest.mark.asyncio
    async def test_cascading_failure_protection(self, failure_breaker):
        """Test protection against cascading failures"""
        # Simulate cascading failure scenario
        async def failing_service():
            raise Exception("Service unavailable")

        # Multiple rapid failures
        for _ in range(5):
            with pytest.raises(Exception):
                await failure_breaker.execute(failing_service)

        # Circuit should be open, protecting against further cascading
        assert failure_breaker.is_open()

        # Subsequent calls should be rejected immediately
        for _ in range(3):
            with pytest.raises(CircuitBreakerOpenException):
                await failure_breaker.execute(failing_service)

        # Verify rejection metrics
        metrics = failure_breaker.get_metrics()
        assert metrics['rejected_requests'] >= 3

    @pytest.mark.asyncio
    async def test_partial_failure_recovery(self, failure_breaker):
        """Test recovery from partial failure scenarios"""
        # Mix of failures and successes
        operations = [
            ("success", None),
            ("success", None),
            ("failure", Exception("Partial failure 1")),
            ("success", None),
            ("failure", Exception("Partial failure 2")),
            ("failure", Exception("Partial failure 3")),  # Should trip
        ]

        for op_type, exception in operations:
            if op_type == "success":
                await failure_breaker.on_success()
            else:
                await failure_breaker.on_failure(exception)

        assert failure_breaker.is_open()

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Partial recovery - some successes, some failures
        recovery_ops = [
            ("success", None),
            ("failure", Exception("Recovery failure")),
            ("success", None),
        ]

        for op_type, exception in recovery_ops:
            if op_type == "success":
                async def success_func():
                    return "success"
                await failure_breaker.execute(success_func)
            else:
                async def failure_func():
                    raise exception
                with pytest.raises(Exception):
                    await failure_breaker.execute(failure_func)

        # Should still be in half-open or open state due to failure
        assert failure_breaker.is_open()

    @pytest.mark.asyncio
    async def test_high_frequency_failures(self, failure_breaker):
        """Test behavior under high-frequency failure conditions"""
        # Rapid succession of failures
        start_time = time.time()

        for i in range(10):
            await failure_breaker.on_failure(Exception(f"Rapid failure {i}"))

        duration = time.time() - start_time

        # Should trip quickly
        assert failure_breaker.is_open()
        assert duration < 0.1  # Should complete very quickly

        # Verify failure count
        assert failure_breaker.failure_count >= failure_breaker.failure_threshold

    @pytest.mark.asyncio
    async def test_failure_rate_adaptation(self, failure_breaker):
        """Test how failure rate affects adaptive thresholds"""
        # Start with good performance
        for _ in range(20):
            await failure_breaker.on_success()

        initial_threshold = failure_breaker.failure_threshold

        # Introduce failures to test adaptation
        failure_rates = [0.1, 0.3, 0.7, 0.9]  # Increasing failure rates

        for rate in failure_rates:
            # Simulate requests with given failure rate
            for i in range(20):
                if i / 20 < rate:
                    await failure_breaker.on_failure(Exception("Rate test failure"))
                else:
                    await failure_breaker.on_success()

            # Threshold should adapt based on failure rate
            current_threshold = failure_breaker.failure_threshold

            if rate < 0.2:
                # Low failure rate - threshold should decrease or stay low
                assert current_threshold <= initial_threshold
            elif rate > 0.8:
                # High failure rate - threshold should increase
                assert current_threshold >= initial_threshold


class TestHalfOpenStateTransitions:
    """Test detailed half-open state transition behavior"""

    @pytest.fixture
    def half_open_breaker(self):
        """Create circuit breaker for half-open state testing"""
        return ProductionCircuitBreaker(
            name="half_open_test",
            failure_threshold=3,
            recovery_timeout=1,
            success_threshold=2,  # Require 2 successes to close
            adaptive_thresholds=True
        )

    @pytest.mark.asyncio
    async def test_half_open_single_success_transition(self, half_open_breaker):
        """Test single success in half-open doesn't immediately close"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # Single success
        await half_open_breaker.on_success()

        # Should remain half-open
        assert half_open_breaker.is_half_open()
        assert half_open_breaker.half_open_success_count == 1

    @pytest.mark.asyncio
    async def test_half_open_multiple_successes_close_circuit(self, half_open_breaker):
        """Test multiple successes in half-open close the circuit"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # First success
        await half_open_breaker.on_success()
        assert half_open_breaker.is_half_open()
        assert half_open_breaker.half_open_success_count == 1

        # Second success - should close circuit
        await half_open_breaker.on_success()
        assert half_open_breaker.is_closed()
        assert half_open_breaker.half_open_success_count == 0
        assert half_open_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_immediate_reopen(self, half_open_breaker):
        """Test failure in half-open immediately reopens circuit"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # Partial success
        await half_open_breaker.on_success()
        assert half_open_breaker.is_half_open()
        assert half_open_breaker.half_open_success_count == 1

        # Failure should immediately reopen
        await half_open_breaker.on_failure(Exception("Half-open failure"))
        assert half_open_breaker.is_open()
        assert half_open_breaker.half_open_success_count == 0
        assert half_open_breaker.failure_count == 1

    @pytest.mark.asyncio
    async def test_half_open_success_failure_interleave(self, half_open_breaker):
        """Test success/failure interleave in half-open state"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # Success, failure, success pattern
        await half_open_breaker.on_success()  # Count: 1
        assert half_open_breaker.is_half_open()

        await half_open_breaker.on_failure(Exception("Interleave failure"))  # Should reopen
        assert half_open_breaker.is_open()
        assert half_open_breaker.half_open_success_count == 0

        # Wait for recovery and try again
        await asyncio.sleep(1.1)
        can_execute = await half_open_breaker.can_execute()
        assert can_execute
        assert half_open_breaker.is_half_open()

        # Now try success pattern
        await half_open_breaker.on_success()  # Count: 1
        await half_open_breaker.on_success()  # Count: 2 - should close
        assert half_open_breaker.is_closed()

    @pytest.mark.asyncio
    async def test_half_open_timeout_behavior(self, half_open_breaker):
        """Test timeout behavior while in half-open state"""
        # Trip circuit first
        for _ in range(4):
            await half_open_breaker.on_failure(Exception("Trip"))

        assert half_open_breaker.is_open()

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Transition to half-open
        can_execute = await half_open_breaker.can_execute()
        assert can_execute
        assert half_open_breaker.is_half_open()

        # In half-open, timeout should not affect state
        await asyncio.sleep(2)  # Wait longer than recovery timeout

        # Should still be half-open
        assert half_open_breaker.is_half_open()

        # Only success/failure should change state
        await half_open_breaker.on_success()
        await half_open_breaker.on_success()
        assert half_open_breaker.is_closed()

    @pytest.mark.asyncio
    async def test_half_open_concurrent_requests(self, half_open_breaker):
        """Test concurrent requests in half-open state"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        async def concurrent_request(success: bool):
            if success:
                await half_open_breaker.on_success()
            else:
                await half_open_breaker.on_failure(Exception("Concurrent failure"))

        # Run concurrent requests
        tasks = [
            asyncio.create_task(concurrent_request(True)),
            asyncio.create_task(concurrent_request(True)),
            asyncio.create_task(concurrent_request(False)),  # This should reopen
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # Due to concurrency, final state may vary, but should be either half-open or open
        assert half_open_breaker.state in [CircuitState.HALF_OPEN, CircuitState.OPEN]

    @pytest.mark.asyncio
    async def test_half_open_metrics_tracking(self, half_open_breaker):
        """Test metrics tracking during half-open transitions"""
        initial_metrics = half_open_breaker.get_metrics()

        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # Perform operations
        await half_open_breaker.on_success()
        await half_open_breaker.on_failure(Exception("Metrics test"))
        await half_open_breaker.on_success()
        await half_open_breaker.on_success()  # Should close

        final_metrics = half_open_breaker.get_metrics()

        # Verify metrics are updated
        assert final_metrics['total_requests'] > initial_metrics['total_requests']
        assert final_metrics['successful_requests'] > initial_metrics['successful_requests']
        assert final_metrics['failed_requests'] > initial_metrics['failed_requests']
        assert final_metrics['state_changes'] >= initial_metrics['state_changes']

    @pytest.mark.asyncio
    async def test_half_open_adaptive_threshold_interaction(self, half_open_breaker):
        """Test interaction between half-open state and adaptive thresholds"""
        # Build good performance history
        for _ in range(30):
            await half_open_breaker.on_success()

        initial_threshold = half_open_breaker.failure_threshold
        assert initial_threshold < 3  # Should be reduced

        # Trip circuit
        for _ in range(initial_threshold + 1):
            await half_open_breaker.on_failure(Exception("Trip"))

        assert half_open_breaker.is_open()

        # Wait for recovery
        await asyncio.sleep(1.1)

        # Transition to half-open
        can_execute = await half_open_breaker.can_execute()
        assert can_execute
        assert half_open_breaker.is_half_open()

        # Successful recovery should maintain good threshold
        await half_open_breaker.on_success()
        await half_open_breaker.on_success()

        assert half_open_breaker.is_closed()
        # Threshold should remain favorable or improve
        assert half_open_breaker.failure_threshold <= initial_threshold

    @pytest.mark.asyncio
    async def test_half_open_state_persistence(self, half_open_breaker):
        """Test half-open state persistence across operations"""
        # Set to half-open state
        half_open_breaker.state = CircuitState.HALF_OPEN

        # Perform multiple operations without closing
        for i in range(5):
            if i < 4:  # Only one success needed for this test
                await half_open_breaker.on_success()
                assert half_open_breaker.is_half_open()
                assert half_open_breaker.half_open_success_count == i + 1

        # Should still be half-open until success_threshold is reached
        assert half_open_breaker.is_half_open()
        assert half_open_breaker.half_open_success_count < half_open_breaker.success_threshold

        # Final success to close
        await half_open_breaker.on_success()
        assert half_open_breaker.is_closed()


class TestCircuitBreakerPool:
    """Test circuit breaker pool functionality"""

    @pytest.fixture
    def pool(self):
        """Create a circuit breaker pool for testing"""
        return CircuitBreakerPool()

    @pytest.fixture
    def adaptive_config(self):
        """Create adaptive timeout configuration"""
        return AdaptiveTimeoutConfig(
            base_timeout=5.0,
            min_timeout=1.0,
            max_timeout=30.0,
            adaptation_factor=0.2,
            strategy=TimeoutStrategy.ADAPTIVE
        )

    @pytest.mark.asyncio
    async def test_pool_initialization(self, pool):
        """Test pool initialization"""
        assert pool._provider_breakers == {}
        assert pool._adaptation_interval == 60
        metrics = pool.get_pool_metrics()
        assert metrics["total_providers"] == 0
        assert metrics["active_breakers"] == 0

    @pytest.mark.asyncio
    async def test_get_provider_breaker_creation(self, pool, adaptive_config):
        """Test provider breaker creation"""
        provider_name = "test_provider"

        # Get breaker (should create new one)
        breaker = await pool.get_provider_breaker(provider_name, adaptive_config)

        assert isinstance(breaker, ProviderCircuitBreaker)
        assert breaker.provider_name == provider_name
        assert breaker.current_timeout == adaptive_config.base_timeout

        # Get same breaker again (should return existing)
        breaker2 = await pool.get_provider_breaker(provider_name)
        assert breaker is breaker2

        # Verify pool metrics
        metrics = pool.get_pool_metrics()
        assert metrics["total_providers"] == 1
        assert metrics["active_breakers"] == 1

    @pytest.mark.asyncio
    async def test_execute_with_breaker_success(self, pool):
        """Test successful execution through pool"""
        provider_name = "success_provider"

        async def success_func():
            return "success_result"

        result = await pool.execute_with_breaker(provider_name, success_func)
        assert result == "success_result"

        # Verify breaker was created and tracked execution
        breaker = await pool.get_provider_breaker(provider_name)
        assert len(breaker.request_history) == 1

    @pytest.mark.asyncio
    async def test_execute_with_breaker_failure(self, pool):
        """Test failed execution through pool"""
        provider_name = "failure_provider"

        async def failure_func():
            raise Exception("Test failure")

        with pytest.raises(Exception, match="Test failure"):
            await pool.execute_with_breaker(provider_name, failure_func)

        # Verify breaker tracked the failure
        breaker = await pool.get_provider_breaker(provider_name)
        assert len(breaker.request_history) == 1

    @pytest.mark.asyncio
    async def test_execute_with_breaker_circuit_open(self, pool):
        """Test execution when circuit is open"""
        provider_name = "open_provider"

        # Trip the circuit
        breaker = await pool.get_provider_breaker(provider_name)
        for _ in range(6):  # More than threshold
            await breaker.circuit_breaker.on_failure(Exception("Trip"))

        assert breaker.circuit_breaker.is_open()

        # Execution should be rejected
        async def test_func():
            return "should not execute"

        with pytest.raises(CircuitBreakerOpenException):
            await pool.execute_with_breaker(provider_name, test_func)

    @pytest.mark.asyncio
    async def test_adaptive_timeout_strategies(self, pool):
        """Test different adaptive timeout strategies"""
        configs = [
            AdaptiveTimeoutConfig(strategy=TimeoutStrategy.ADAPTIVE),
            AdaptiveTimeoutConfig(strategy=TimeoutStrategy.QUANTILE),
            AdaptiveTimeoutConfig(strategy=TimeoutStrategy.FIXED),
        ]

        for i, config in enumerate(configs):
            provider_name = f"adaptive_provider_{i}"
            breaker = await pool.get_provider_breaker(provider_name, config)

            # Add some request history
            breaker.request_history = [1.0, 2.0, 3.0, 4.0, 5.0]

            # Adapt timeout
            await pool.adapt_provider_timeout(provider_name)

            # Verify timeout was adapted (or remained fixed)
            if config.strategy == TimeoutStrategy.FIXED:
                assert breaker.current_timeout == config.base_timeout
            else:
                # Should have adapted
                assert breaker.current_timeout != config.base_timeout

    @pytest.mark.asyncio
    async def test_timeout_adaptation_bounds(self, pool):
        """Test timeout adaptation respects bounds"""
        config = AdaptiveTimeoutConfig(
            base_timeout=10.0,
            min_timeout=2.0,
            max_timeout=20.0,
            strategy=TimeoutStrategy.ADAPTIVE
        )

        provider_name = "bounds_provider"
        breaker = await pool.get_provider_breaker(provider_name, config)

        # Very slow responses to test upper bound
        breaker.request_history = [25.0] * 20  # Very slow
        await pool.adapt_provider_timeout(provider_name)
        assert breaker.current_timeout <= config.max_timeout

        # Reset and test lower bound
        breaker.current_timeout = 10.0
        breaker.request_history = [0.5] * 20  # Very fast
        await pool.adapt_provider_timeout(provider_name)
        assert breaker.current_timeout >= config.min_timeout

    @pytest.mark.asyncio
    async def test_get_provider_timeout(self, pool, adaptive_config):
        """Test getting provider timeout"""
        provider_name = "timeout_provider"

        # Before creation
        timeout = pool.get_provider_timeout(provider_name)
        assert timeout == pool._default_config.base_timeout

        # After creation
        breaker = await pool.get_provider_breaker(provider_name, adaptive_config)
        timeout = pool.get_provider_timeout(provider_name)
        assert timeout == adaptive_config.base_timeout

    @pytest.mark.asyncio
    async def test_pool_metrics_comprehensive(self, pool):
        """Test comprehensive pool metrics"""
        # Create multiple providers
        providers = ["provider_1", "provider_2", "provider_3"]

        for provider in providers:
            breaker = await pool.get_provider_breaker(provider)

            # Simulate some activity
            if provider == "provider_1":
                # Successful provider
                for _ in range(5):
                    await breaker.circuit_breaker.on_success()
            elif provider == "provider_2":
                # Failed provider
                for _ in range(6):
                    await breaker.circuit_breaker.on_failure(Exception("Test"))
            # provider_3 remains idle

        metrics = pool.get_pool_metrics()

        assert metrics["total_providers"] == 3
        assert metrics["active_breakers"] == 3
        assert "providers" in metrics

        # Check individual provider metrics
        provider_metrics = metrics["providers"]
        assert "provider_1" in provider_metrics
        assert "provider_2" in provider_metrics
        assert "provider_3" in provider_metrics

        # Verify tripped breakers count
        assert metrics["tripped_breakers"] >= 1  # provider_2 should be tripped

    @pytest.mark.asyncio
    async def test_get_provider_status(self, pool):
        """Test getting individual provider status"""
        provider_name = "status_provider"

        # Before creation
        status = pool.get_provider_status(provider_name)
        assert status["status"] == "not_found"

        # After creation
        breaker = await pool.get_provider_breaker(provider_name)

        # Simulate some activity
        for _ in range(3):
            await breaker.circuit_breaker.on_success()

        status = pool.get_provider_status(provider_name)

        assert status["provider_name"] == provider_name
        assert "circuit_state" in status
        assert "current_timeout" in status
        assert "failure_count" in status
        assert "success_rate" in status

    @pytest.mark.asyncio
    async def test_reset_provider_breaker(self, pool):
        """Test resetting individual provider breaker"""
        provider_name = "reset_provider"

        breaker = await pool.get_provider_breaker(provider_name)

        # Trip the circuit and add history
        for _ in range(6):
            await breaker.circuit_breaker.on_failure(Exception("Trip"))

        breaker.request_history = [1.0, 2.0, 3.0]
        breaker.current_timeout = 15.0

        assert breaker.circuit_breaker.is_open()
        assert len(breaker.request_history) == 3
        assert breaker.current_timeout == 15.0

        # Reset
        await pool.reset_provider_breaker(provider_name)

        # Verify reset
        assert breaker.circuit_breaker.is_closed()
        assert len(breaker.request_history) == 0
        assert breaker.current_timeout == breaker.adaptive_config.base_timeout

    @pytest.mark.asyncio
    async def test_adaptation_loop_functionality(self, pool):
        """Test adaptation loop functionality"""
        # Create providers
        providers = ["loop_provider_1", "loop_provider_2"]
        for provider in providers:
            breaker = await pool.get_provider_breaker(provider)
            breaker.request_history = [1.0, 2.0, 3.0] * 10  # Add history

        # Start adaptation loop
        await pool.start_adaptation_loop()

        # Wait a bit for adaptation
        await asyncio.sleep(0.1)

        # Stop adaptation loop
        await pool.stop_adaptation_loop()

        # Verify adaptations occurred
        for provider in providers:
            breaker = await pool.get_provider_breaker(provider)
            # Timeout should have been adapted
            assert breaker.current_timeout != breaker.adaptive_config.base_timeout

    @pytest.mark.asyncio
    async def test_multiple_provider_isolation(self, pool):
        """Test that provider breakers are isolated"""
        providers = ["isolated_1", "isolated_2", "isolated_3"]

        # Create all breakers
        breakers = {}
        for provider in providers:
            breakers[provider] = await pool.get_provider_breaker(provider)

        # Trip one provider
        tripped_breaker = breakers["isolated_1"]
        for _ in range(6):
            await tripped_breaker.circuit_breaker.on_failure(Exception("Trip isolated_1"))

        assert tripped_breaker.circuit_breaker.is_open()

        # Others should remain closed
        for provider in ["isolated_2", "isolated_3"]:
            assert breakers[provider].circuit_breaker.is_closed()

        # Test execution isolation
        async def success_func():
            return "success"

        # Tripped provider should reject
        with pytest.raises(CircuitBreakerOpenException):
            await pool.execute_with_breaker("isolated_1", success_func)

        # Others should work
        for provider in ["isolated_2", "isolated_3"]:
            result = await pool.execute_with_breaker(provider, success_func)
            assert result == "success"


class TestRealisticFailurePatterns:
    """Integration tests with realistic failure patterns"""

    @pytest.fixture
    def realistic_pool(self):
        """Create pool with realistic configuration"""
        pool = CircuitBreakerPool()
        pool._adaptation_interval = 5  # Faster adaptation for testing
        return pool

    @pytest.mark.asyncio
    async def test_network_timeout_simulation(self, realistic_pool):
        """Simulate network timeout failures"""
        provider_name = "network_provider"

        async def network_call(delay: float, should_timeout: bool = False):
            if should_timeout:
                await asyncio.sleep(delay + 10)  # Much longer than timeout
            else:
                await asyncio.sleep(delay)
            return f"response_after_{delay}s"

        # Simulate network timeouts
        timeouts = 0
        for i in range(10):
            try:
                if i < 7:  # First 7 calls timeout
                    await realistic_pool.execute_with_breaker(
                        provider_name, network_call, 5.0, True
                    )
                else:  # Last 3 succeed
                    result = await realistic_pool.execute_with_breaker(
                        provider_name, network_call, 1.0, False
                    )
                    assert "response_after" in result
            except asyncio.TimeoutError:
                timeouts += 1
            except CircuitBreakerOpenException:
                timeouts += 1  # Count rejections as timeouts

        # Should have tripped due to timeouts
        breaker = await realistic_pool.get_provider_breaker(provider_name)
        assert breaker.circuit_breaker.is_open()

    @pytest.mark.asyncio
    async def test_service_degradation_pattern(self, realistic_pool):
        """Simulate gradual service degradation"""
        provider_name = "degrading_provider"

        async def degrading_service(quality: float):
            """Service with variable quality"""
            if quality < 0.3:  # Poor quality
                await asyncio.sleep(5.0)  # Slow response
                return "slow_response"
            elif quality < 0.7:  # Medium quality
                await asyncio.sleep(1.0)
                if quality < 0.5:  # Sometimes fail
                    raise Exception("Intermittent failure")
                return "medium_response"
            else:  # Good quality
                await asyncio.sleep(0.1)
                return "fast_response"

        # Simulate degradation over time
        quality_levels = [0.9, 0.8, 0.6, 0.4, 0.2, 0.1, 0.3, 0.5, 0.7, 0.8]

        for quality in quality_levels:
            try:
                result = await realistic_pool.execute_with_breaker(
                    provider_name, degrading_service, quality
                )
                assert "response" in result
            except Exception:
                pass  # Expected for low quality

        # Check adaptive behavior
        breaker = await realistic_pool.get_provider_breaker(provider_name)
        initial_timeout = breaker.adaptive_config.base_timeout
        current_timeout = breaker.current_timeout

        # Timeout should have adapted due to slow responses
        assert current_timeout != initial_timeout

    @pytest.mark.asyncio
    async def test_burst_traffic_with_failures(self, realistic_pool):
        """Test burst traffic patterns with intermittent failures"""
        provider_name = "burst_provider"

        async def burst_service(request_id: int, fail_probability: float):
            """Service that fails based on probability"""
            if request_id % 10 == 0:  # Every 10th request has higher failure chance
                fail_probability *= 2

            if fail_probability > 0.7:  # High failure rate
                raise Exception(f"Burst failure {request_id}")

            await asyncio.sleep(0.05)  # Small delay
            return f"success_{request_id}"

        # Simulate burst traffic
        tasks = []
        fail_probabilities = [0.1, 0.2, 0.5, 0.8, 0.3, 0.1] * 20  # Repeating pattern

        for i, fail_prob in enumerate(fail_probabilities):
            tasks.append(
                realistic_pool.execute_with_breaker(
                    provider_name, burst_service, i, fail_prob
                )
            )

        # Execute burst
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successes and failures
        successes = sum(1 for r in results if not isinstance(r, Exception))
        failures = sum(1 for r in results if isinstance(r, Exception))

        # Should have some failures but not complete failure
        assert successes > 0
        assert failures > 0
        assert successes + failures == len(fail_probabilities)

    @pytest.mark.asyncio
    async def test_multi_provider_failover_scenario(self, realistic_pool):
        """Test failover between multiple providers"""
        providers = ["primary_provider", "backup_provider", "tertiary_provider"]

        async def provider_service(provider_name: str, is_healthy: bool):
            if not is_healthy:
                raise Exception(f"{provider_name} is down")
            await asyncio.sleep(0.1)
            return f"response_from_{provider_name}"

        # Simulate provider health states
        health_states = {
            "primary_provider": [True] * 10 + [False] * 20,  # Initially healthy, then fails
            "backup_provider": [False] * 15 + [True] * 15,    # Initially down, then recovers
            "tertiary_provider": [True] * 30                   # Always healthy
        }

        # Simulate requests with failover logic
        successful_requests = 0
        failed_requests = 0

        for i in range(30):
            request_succeeded = False

            for provider in providers:
                is_healthy = health_states[provider][i]
                try:
                    result = await realistic_pool.execute_with_breaker(
                        provider, provider_service, provider, is_healthy
                    )
                    successful_requests += 1
                    request_succeeded = True
                    break  # Success, no need to try other providers
                except (Exception, CircuitBreakerOpenException):
                    continue  # Try next provider

            if not request_succeeded:
                failed_requests += 1

        # Should have high success rate due to failover
        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        assert success_rate > 0.8  # At least 80% success rate with failover

    @pytest.mark.asyncio
    async def test_adaptive_recovery_under_load(self, realistic_pool):
        """Test adaptive recovery behavior under continuous load"""
        provider_name = "load_recovery_provider"

        async def load_service(iteration: int):
            # Pattern: fail for first 10, succeed for next 5, fail for next 10, etc.
            cycle_position = iteration % 25
            if cycle_position < 10 or (15 <= cycle_position < 25):
                raise Exception(f"Load failure at iteration {iteration}")
            else:
                await asyncio.sleep(0.05)
                return f"success_{iteration}"

        # Continuous load simulation
        tasks = []
        for i in range(50):
            tasks.append(
                realistic_pool.execute_with_breaker(provider_name, load_service, i)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]

        # Should have both successes and failures
        assert len(successes) > 0
        assert len(failures) > 0

        # Check circuit breaker state
        breaker = await realistic_pool.get_provider_breaker(provider_name)

        # Should have experienced state changes
        metrics = breaker.circuit_breaker.get_metrics()
        assert metrics['state_changes'] > 0

        # Adaptive timeout should have adjusted
        assert breaker.current_timeout != breaker.adaptive_config.base_timeout

    @pytest.mark.asyncio
    async def test_realistic_timeout_adaptation(self, realistic_pool):
        """Test timeout adaptation with realistic response times"""
        provider_name = "timeout_adapt_provider"

        async def variable_delay_service(delay: float, should_fail: bool = False):
            if should_fail:
                raise Exception("Service failure")
            await asyncio.sleep(delay)
            return f"delayed_response_{delay}"

        # Simulate realistic response time distribution
        response_times = [
            0.1, 0.15, 0.2, 0.12, 0.18,  # Fast responses
            2.0, 2.5, 3.0, 1.8, 2.2,      # Slow responses
            0.08, 0.12, 0.15,             # Fast again
            5.0, 6.0,                     # Very slow (should trigger adaptation)
        ]

        for delay in response_times:
            try:
                result = await realistic_pool.execute_with_breaker(
                    provider_name, variable_delay_service, delay, False
                )
                assert "delayed_response" in result
            except Exception:
                pass

        # Check timeout adaptation
        breaker = await realistic_pool.get_provider_breaker(provider_name)
        initial_timeout = breaker.adaptive_config.base_timeout
        adapted_timeout = breaker.current_timeout

        # Should have increased timeout due to slow responses
        assert adapted_timeout > initial_timeout

        # But should not exceed max timeout
        assert adapted_timeout <= breaker.adaptive_config.max_timeout

    @pytest.mark.asyncio
    async def test_cascading_failure_prevention(self, realistic_pool):
        """Test prevention of cascading failures across providers"""
        providers = [f"cascading_provider_{i}" for i in range(5)]

        async def cascading_service(provider_name: str, iteration: int):
            # First provider fails consistently, others have varying reliability
            provider_index = int(provider_name.split('_')[-1])

            if provider_index == 0:  # Primary always fails
                raise Exception("Primary failure")
            elif iteration % (provider_index + 1) == 0:  # Others fail occasionally
                raise Exception(f"Intermittent failure {provider_name}")
            else:
                await asyncio.sleep(0.05)
                return f"success_{provider_name}_{iteration}"

        # Simulate load across all providers
        tasks = []
        for i in range(20):
            for provider in providers:
                tasks.append(
                    realistic_pool.execute_with_breaker(
                        provider, cascading_service, provider, i
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results per provider
        provider_results = {}
        for provider in providers:
            provider_results[provider] = []

        for i, result in enumerate(results):
            provider_index = i % len(providers)
            provider = providers[provider_index]
            provider_results[provider].append(result)

        # Primary should be tripped
        primary_breaker = await realistic_pool.get_provider_breaker(providers[0])
        assert primary_breaker.circuit_breaker.is_open()

        # Others should have mixed results but not all failed
        for provider in providers[1:]:
            breaker = await realistic_pool.get_provider_breaker(provider)
            provider_successes = sum(1 for r in provider_results[provider]
                                   if not isinstance(r, Exception))
            # Should have some successes
            assert provider_successes > 0
