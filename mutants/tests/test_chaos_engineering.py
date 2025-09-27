"""
Tests for chaos engineering framework and fault injection.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import httpx

from src.core.chaos_engineering import (
    ChaosMonkey, NetworkSimulator, FaultType, Severity, FaultConfig,
    chaos_monkey, network_simulator, run_chaos_scenario
)


class TestChaosMonkey:
    """Test the chaos engineering framework."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chaos = ChaosMonkey()
        
    def test_initialization(self):
        """Test chaos monkey initialization."""
        assert not self.chaos.enabled
        assert len(self.chaos.active_faults) == 0
        assert len(self.chaos.injection_history) == 0
        
    def test_configure_chaos_engineering(self):
        """Test chaos engineering configuration."""
        config = {
            "enabled": True,
            "faults": [
                {
                    "type": "delay",
                    "severity": "medium",
                    "probability": 0.1,
                    "duration_ms": 100,
                    "error_code": 503,
                    "error_message": "Test error"
                }
            ]
        }
        
        self.chaos.configure(config)
        assert self.chaos.enabled
        assert len(self.chaos.active_faults) == 1
        
    def test_fault_probability(self):
        """Test fault probability calculation."""
        fault_config = FaultConfig(
            fault_type=FaultType.DELAY,
            severity=Severity.LOW,
            probability=0.0
        )
        
        assert not self.chaos.should_inject_fault(fault_config)
        
        fault_config.probability = 1.0
        assert self.chaos.should_inject_fault(fault_config)
        
    @pytest.mark.asyncio
    async def test_delay_fault_injection(self):
        """Test delay fault injection."""
        fault_config = FaultConfig(
            fault_type=FaultType.DELAY,
            severity=Severity.LOW,
            probability=1.0,
            duration_ms=100
        )
        
        start_time = asyncio.get_event_loop().time()
        error = await self.chaos.inject_fault(fault_config)
        end_time = asyncio.get_event_loop().time()
        
        assert error is None
        assert end_time - start_time >= 0.1  # 100ms delay
        
    @pytest.mark.asyncio
    async def test_error_fault_injection(self):
        """Test error fault injection."""
        fault_config = FaultConfig(
            fault_type=FaultType.ERROR,
            severity=Severity.MEDIUM,
            probability=1.0,
            duration_ms=0,
            error_code=503,
            error_message="Service unavailable"
        )
        
        error = await self.chaos.inject_fault(fault_config)
        
        assert error is not None
        assert isinstance(error, httpx.HTTPStatusError)
        assert error.response.status_code == 503
        
    @pytest.mark.asyncio
    async def test_timeout_fault_injection(self):
        """Test timeout fault injection."""
        fault_config = FaultConfig(
            fault_type=FaultType.TIMEOUT,
            severity=Severity.HIGH,
            probability=1.0,
            duration_ms=50  # Short timeout for testing
        )
        
        error = await self.chaos.inject_fault(fault_config)
        
        assert error is not None
        assert isinstance(error, asyncio.TimeoutError)
        
    @pytest.mark.asyncio
    async def test_rate_limit_fault_injection(self):
        """Test rate limit fault injection."""
        fault_config = FaultConfig(
            fault_type=FaultType.RATE_LIMIT,
            severity=Severity.LOW,
            probability=1.0
        )
        
        error = await self.chaos.inject_fault(fault_config)
        
        assert error is not None
        assert isinstance(error, httpx.HTTPStatusError)
        assert error.response.status_code == 429
        
    @pytest.mark.asyncio
    async def test_network_failure_fault_injection(self):
        """Test network failure fault injection."""
        fault_config = FaultConfig(
            fault_type=FaultType.NETWORK_FAILURE,
            severity=Severity.CRITICAL,
            probability=1.0
        )
        
        error = await self.chaos.inject_fault(fault_config)
        
        assert error is not None
        assert isinstance(error, ConnectionError)
        
    def test_injection_statistics(self):
        """Test injection statistics collection."""
        self.chaos.configure({
            "enabled": True,
            "faults": [
                {"type": "delay", "severity": "low", "probability": 1.0, "duration_ms": 100}
            ]
        })
        
        stats = self.chaos.get_injection_stats()
        assert "total_injections" in stats
        assert "active_faults" in stats
        
    def test_reset_functionality(self):
        """Test chaos reset functionality."""
        self.chaos.configure({
            "enabled": True,
            "faults": [{"type": "delay", "severity": "low", "probability": 1.0, "duration_ms": 100}]
        })
        
        self.chaos.reset()
        assert not self.chaos.enabled
        assert len(self.chaos.active_faults) == 0
        assert len(self.chaos.injection_history) == 0
        
    @pytest.mark.asyncio
    async def test_chaos_context_manager(self):
        """Test chaos context manager."""
        self.chaos.configure({
            "enabled": True,
            "faults": [{"type": "delay", "severity": "low", "probability": 0.0, "duration_ms": 100}]
        })
        
        # No fault should be injected with 0 probability
        async with self.chaos.chaos_context("test_operation"):
            assert True  # Should complete without issues
            
    @pytest.mark.asyncio
    async def test_chaos_context_with_fault(self):
        """Test chaos context manager with fault injection."""
        self.chaos.configure({
            "enabled": True,
            "faults": [{"type": "timeout", "severity": "high", "probability": 1.0, "duration_ms": 10}]
        })
        
        with pytest.raises(asyncio.TimeoutError):
            async with self.chaos.chaos_context("test_operation"):
                pass  # Should raise timeout


class TestNetworkSimulator:
    """Test network simulation utilities."""
    
    @pytest.mark.asyncio
    async def test_simulate_delay(self):
        """Test network delay simulation."""
        start_time = asyncio.get_event_loop().time()
        await network_simulator.simulate_delay(50)  # 50ms
        end_time = asyncio.get_event_loop().time()
        
        assert end_time - start_time >= 0.05
        
    @pytest.mark.asyncio
    async def test_simulate_jitter(self):
        """Test network jitter simulation."""
        base_delay = 100
        jitter_percent = 0.2
        
        # Test multiple times to verify jitter
        delays = []
        for _ in range(10):
            start_time = asyncio.get_event_loop().time()
            await network_simulator.simulate_jitter(base_delay, jitter_percent)
            end_time = asyncio.get_event_loop().time()
            delays.append(end_time - start_time)
            
        # All delays should be within jitter bounds
        for delay in delays:
            assert 0.08 <= delay <= 0.12  # ±20% of 100ms
            
    def test_network_profiles(self):
        """Test predefined network profiles."""
        profiles = network_simulator.get_network_profiles()
        
        assert "fast" in profiles
        assert "medium" in profiles
        assert "slow" in profiles
        assert "unreliable" in profiles
        
        fast_profile = profiles["fast"]
        assert fast_profile["min_delay"] == 10
        assert fast_profile["max_delay"] == 50
        
    def test_network_profile_ranges(self):
        """Test network profile value ranges."""
        profiles = network_simulator.get_network_profiles()
        
        for name, profile in profiles.items():
            assert profile["min_delay"] >= 0
            assert profile["max_delay"] >= profile["min_delay"]
            assert 0 <= profile["jitter"] <= 1


class TestChaosScenarioRunner:
    """Test chaos scenario runner."""
    
    @pytest.mark.asyncio
    async def test_successful_chaos_scenario(self):
        """Test successful chaos scenario execution."""
        scenario_config = {
            "enabled": False,
            "faults": []
        }
        
        async def target_function():
            return {"status": "success", "data": "test"}
            
        result = await run_chaos_scenario(scenario_config, target_function)
        
        assert result["success"] is True
        assert result["result"]["status"] == "success"
        assert "duration_ms" in result
        assert "chaos_injections" in result
        
    @pytest.mark.asyncio
    async def test_failed_chaos_scenario(self):
        """Test failed chaos scenario execution."""
        scenario_config = {
            "enabled": True,
            "faults": [
                {"type": "error", "severity": "medium", "probability": 1.0, "error_code": 500}
            ]
        }
        
        async def target_function():
            raise ValueError("Simulated error")
            
        result = await run_chaos_scenario(scenario_config, target_function)
        
        assert result["success"] is False
        assert "error" in result
        assert "duration_ms" in result
        assert "chaos_injections" in result
        
    @pytest.mark.asyncio
    async def test_chaos_scenario_with_delay(self):
        """Test chaos scenario with delay."""
        scenario_config = {
            "enabled": True,
            "faults": [{"type": "delay", "severity": "low", "probability": 1.0, "duration_ms": 100}]
        }
        
        async def target_function():
            await asyncio.sleep(0.001)
            return {"delayed": True}
            
        result = await run_chaos_scenario(scenario_config, target_function)
        
        assert result["success"] is True
        assert result["result"]["delayed"] is True
        # Should include delay in duration
        assert result["duration_ms"] > 100


class TestChaosMonkeyIntegration:
    """Test chaos monkey integration with the application."""
    
    def test_chaos_monkey_global_instance(self):
        """Test global chaos monkey instance."""
        assert chaos_monkey is not None
        assert isinstance(chaos_monkey, ChaosMonkey)
        
    def test_network_simulator_global_instance(self):
        """Test global network simulator instance."""
        assert network_simulator is not None
        assert isinstance(network_simulator, NetworkSimulator)


class TestPerformanceUnderChaos:
    """Test performance characteristics under chaos conditions."""
    
    @pytest.mark.asyncio
    async def test_performance_degradation(self):
        """Test performance degradation under chaos."""
        scenario_config = {
            "enabled": True,
            "faults": [
                {"type": "delay", "severity": "medium", "probability": 1.0, "duration_ms": 50}
            ]
        }
        
        async def fast_function():
            return "quick"
            
        # Baseline performance
        import time
        baseline_start = time.time()
        for _ in range(10):
            await fast_function()
        baseline_duration = time.time() - baseline_start
        
        # With chaos
        chaos_start = time.time()
        for _ in range(10):
            await run_chaos_scenario(scenario_config, fast_function)
        chaos_duration = time.time() - chaos_start
        
        # Should show degradation
        assert chaos_duration > baseline_duration
        
    @pytest.mark.asyncio
    async def test_circuit_breaker_with_chaos(self):
        """Test circuit breaker behavior under chaos."""
        trip_count = 0
        
        async def failing_function():
            nonlocal trip_count
            trip_count += 1
            raise ValueError("Chaos induced failure")
            
        scenario_config = {
            "enabled": True,
            "faults": [
                {"type": "error", "severity": "high", "probability": 1.0, "error_code": 503}
            ]
        }
        
        # Run multiple times to trigger circuit breaker
        for _ in range(5):
            result = await run_chaos_scenario(scenario_config, failing_function)
            assert result["success"] is False
            
        # Should have multiple failures
        assert trip_count >= 5