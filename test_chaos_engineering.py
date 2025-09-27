import asyncio
import time
from src.core.chaos.monkey import chaos_monkey, FaultConfig, FaultType, FaultSeverity

async def test_chaos_engineering():
    """Test the chaos engineering framework."""

    print('🐒 TESTANDO CHAOS ENGINEERING FRAMEWORK:')

    try:
        # Configure chaos monkey
        from types import SimpleNamespace
        config = SimpleNamespace()
        config.enabled = True
        config.faults = [
            {
                'type': 'latency',
                'severity': 'medium',
                'probability': 1.0,  # 100% for testing
                'duration_ms': 100,
                'target_services': [],
                'enabled': True
            }
        ]

        chaos_monkey.configure(config)
        print('✅ Chaos Monkey configured')

        # Create a test experiment
        latency_fault = FaultConfig(
            type=FaultType.LATENCY,
            severity=FaultSeverity.MEDIUM,
            probability=1.0,  # Always inject for testing
            duration_ms=200,
            target_services=[],
            enabled=True
        )

        experiment = chaos_monkey.create_experiment(
            name="test_latency_experiment",
            description="Test latency injection",
            duration_minutes=1,  # 1 minute for testing
            faults=[latency_fault]
        )
        print(f'✅ Test experiment created: {experiment.name}')

        # Start the experiment
        success = await chaos_monkey.start_experiment("test_latency_experiment")
        print(f'✅ Experiment started: {success}')

        # Wait a bit for fault injection
        await asyncio.sleep(2)

        # Check active experiments
        active = chaos_monkey.get_active_experiments()
        print(f'✅ Active experiments: {len(active)}')

        # Get safety metrics
        metrics = chaos_monkey.get_safety_metrics()
        print(f'✅ Safety metrics: {metrics}')

        # Stop the experiment
        success = await chaos_monkey.stop_experiment("test_latency_experiment")
        print(f'✅ Experiment stopped: {success}')

        # Check final metrics
        final_metrics = chaos_monkey.get_safety_metrics()
        print(f'✅ Final metrics: {final_metrics}')

        # Shutdown
        await chaos_monkey.shutdown()
        print('✅ Chaos Monkey shutdown complete')

    except Exception as e:
        print(f'❌ Erro no teste: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chaos_engineering())
