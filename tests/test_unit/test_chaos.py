"""
Unit tests for chaos engineering framework.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from src.core.chaos.monkey import (
    ChaosMonkey, ChaosExperiment, FaultConfig,
    FaultType, FaultSeverity, LatencyInjector,
    NetworkFailureInjector, ResourceExhaustionInjector
)


class TestFaultConfig:
    """Test fault configuration."""

    def test_fault_config_creation(self):
        """Test fault configuration creation."""
        config = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.MEDIUM,
            probability=0.1,
            duration_ms=500,
            target_services=["openai"]
        )

        assert config.type == FaultType.LATENCY
        assert config.severity == FaultSeverity.MEDIUM
        assert config.probability == 0.1
        assert config.duration_ms == 500
        assert config.target_services == ["openai"]

    def test_fault_probability(self):
        """Test fault injection probability."""
        config = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.LOW,
            probability=0.0,  # Never inject
            duration_ms=100
        )

        # Should not inject when probability is 0
        for _ in range(100):
            assert not config.should_inject()


class TestLatencyInjector:
    """Test latency injector."""

    @pytest.mark.asyncio
    async def test_latency_injection(self):
        """Test latency injection."""
        config = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.MEDIUM,
            probability=1.0,  # Always inject for testing
            duration_ms=100
        )

        injector = LatencyInjector(config)

        start_time = time.time()
        await injector.inject()
        end_time = time.time()

        # Should have taken at least the configured duration
        elapsed = (end_time - start_time) * 1000  # Convert to ms
        assert elapsed >= 90  # Allow some margin for timing

    def test_service_targeting(self):
        """Test service targeting."""
        config = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.LOW,
            probability=1.0,
            duration_ms=100,
            target_services=["openai"]
        )

        injector = LatencyInjector(config)

        # Should inject for targeted service
        assert injector.should_inject_for_service("openai")

        # Should not inject for non-targeted service
        assert not injector.should_inject_for_service("anthropic")

        # Should inject when no target services specified
        config_no_targets = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.LOW,
            probability=1.0,
            duration_ms=100
        )
        injector_no_targets = LatencyInjector(config_no_targets)
        assert injector_no_targets.should_inject_for_service("any_service")


class TestChaosExperiment:
    """Test chaos experiment."""

    def test_experiment_creation(self):
        """Test experiment creation."""
        faults = [
            FaultConfig(
                type=FaultType.LATENCY,
                severity=FaultSeverity.MEDIUM,
                probability=0.1,
                duration_ms=500
            )
        ]

        experiment = ChaosExperiment(
            name="test_experiment",
            description="Test chaos experiment",
            duration_minutes=5,
            faults=faults
        )

        assert experiment.name == "test_experiment"
        assert experiment.description == "Test chaos experiment"
        assert experiment.duration_minutes == 5
        assert len(experiment.faults) == 1
        assert experiment.status == "pending"


class TestChaosMonkey:
    """Test chaos monkey framework."""

    @pytest.mark.asyncio
    async def test_chaos_monkey_configuration(self):
        """Test chaos monkey configuration."""
        monkey = ChaosMonkey()

        # Test with valid config
        from types import SimpleNamespace
        config = SimpleNamespace()
        config.enabled = True
        config.faults = [
            {
                'type': 'latency',
                'severity': 'medium',
                'probability': 0.1,
                'duration_ms': 500,
                'target_services': [],
                'enabled': True
            }
        ]

        monkey.configure(config)
        assert monkey.enabled is True
        assert len(monkey.fault_injectors) == 1

    @pytest.mark.asyncio
    async def test_experiment_lifecycle(self):
        """Test experiment lifecycle."""
        monkey = ChaosMonkey()

        # Create experiment
        faults = [
            FaultConfig(
                type=FaultType.LATENCY,
                severity=FaultSeverity.LOW,
                probability=1.0,  # Always inject for testing
                duration_ms=50
            )
        ]

        experiment = monkey.create_experiment(
            name="lifecycle_test",
            description="Test experiment lifecycle",
            duration_minutes=1,
            faults=faults
        )

        assert experiment.name in monkey.experiments

        # Start experiment
        success = await monkey.start_experiment("lifecycle_test")
        assert success is True

        # Check active experiments
        active = monkey.get_active_experiments()
        assert "lifecycle_test" in active

        # Stop experiment
        success = await monkey.stop_experiment("lifecycle_test")
        assert success is True

        # Check final status
        final_active = monkey.get_active_experiments()
        assert "lifecycle_test" not in final_active

    @pytest.mark.asyncio
    async def test_emergency_stop(self):
        """Test emergency stop functionality."""
        monkey = ChaosMonkey()

        # Create and start multiple experiments
        for i in range(3):
            experiment = monkey.create_experiment(
                name=f"emergency_test_{i}",
                description=f"Emergency test {i}",
                duration_minutes=5,
                faults=[]
            )
            await monkey.start_experiment(f"emergency_test_{i}")

        # Verify experiments are running
        active = monkey.get_active_experiments()
        assert len(active) == 3

        # Emergency stop
        await monkey.emergency_stop()

        # Verify all experiments stopped
        active = monkey.get_active_experiments()
        assert len(active) == 0

    @pytest.mark.asyncio
    async def test_safety_metrics(self):
        """Test safety metrics collection."""
        monkey = ChaosMonkey()

        # Get initial metrics
        metrics = monkey.get_safety_metrics()

        assert "total_experiments" in metrics
        assert "successful_experiments" in metrics
        assert "failed_experiments" in metrics
        assert "emergency_stops" in metrics
        assert "fault_injections" in metrics

        # All metrics should start at 0
        for key in ["total_experiments", "successful_experiments", "failed_experiments", "emergency_stops", "fault_injections"]:
            assert metrics[key] == 0
