#!/usr/bin/env python3
"""
Test script for adaptive sampling functionality.
Tests the adaptive sampling mechanism under different load conditions.
"""

import asyncio
import time
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from core.metrics import MetricsCollector, metrics_collector
from core.telemetry import telemetry, TracedSpan


def simulate_cpu_load(duration_seconds: int, target_percent: float):
    """Simulate CPU load by busy waiting"""
    end_time = time.time() + duration_seconds

    while time.time() < end_time:
        # Busy wait to consume CPU
        for _ in range(10000):
            _ = 1 + 1


def simulate_memory_load(size_mb: int):
    """Simulate memory usage"""
    # Allocate memory
    memory_blocks = []
    block_size = 1024 * 1024  # 1MB blocks

    for _ in range(size_mb):
        memory_blocks.append(bytearray(block_size))

    return memory_blocks


async def simulate_requests(
    metrics_collector: MetricsCollector, num_requests: int, delay: float = 0.01
):
    """Simulate API requests with telemetry"""
    for i in range(num_requests):
        with TracedSpan(
            f"test_request_{i}", {"provider": "test", "model": "gpt-4"}
        ) as span:
            span.set_attribute("request_id", i)
            span.set_attribute("tokens", 100)

            # Simulate processing time
            await asyncio.sleep(delay)

            # Simulate occasional errors
            if i % 100 == 0:
                span.record_error(Exception("Simulated error"))


async def test_adaptive_sampling():
    """Test adaptive sampling under different load conditions"""
    print("Testing Adaptive Sampling Implementation")
    print("=" * 50)

    # Reset the global metrics collector for testing
    metrics_collector.reset_stats()
    metrics_collector.enable_adaptive_sampling = True
    metrics_collector.sampling_rate = 0.1

    print(f"Initial sampling rate: {metrics_collector.sampling_rate}")
    print(
        f"Adaptive sampling enabled: {metrics_collector.enable_adaptive_sampling}"
    )

    # Test 1: Low load scenario
    print("\n--- Test 1: Low Load Scenario ---")
    print("Simulating low load (CPU < 30%, Memory < 50%)")

    # Background tasks will start automatically when event loop is available
    # Wait for initial system health update
    await asyncio.sleep(35)

    # Simulate low volume requests
    print("Simulating 100 requests at low volume...")
    await simulate_requests(metrics_collector, 100, 0.1)

    # Manually trigger adaptive adjustment since background tasks may not be running
    metrics_collector._adjust_sampling_rate()

    stats = metrics_collector.get_all_stats()
    sampling_info = stats.get("sampling", {})
    adaptive_info = sampling_info.get("adaptive", {})

    print(
        f"Sampling rate after low load: {metrics_collector.sampling_rate:.3f}"
    )
    print(f"Load score: {adaptive_info.get('current_load_score', 0):.3f}")
    print(
        f"Request volume: {adaptive_info.get('current_request_volume', 0):.1f} req/sec"
    )
    print(
        f"Total requests tracked: {len(metrics_collector._request_timestamps)}"
    )

    # Test 2: High load scenario
    print("\n--- Test 2: High Load Scenario ---")
    print("Simulating high load (CPU > 70%, high request volume)")

    # Start CPU load simulation in background
    cpu_thread = threading.Thread(target=simulate_cpu_load, args=(120, 80))
    cpu_thread.start()

    # Simulate high memory usage
    memory_blocks = simulate_memory_load(200)  # 200MB

    # Simulate high volume requests
    print("Simulating 500 requests at high volume...")
    await simulate_requests(metrics_collector, 500, 0.01)

    # Manually trigger adaptive adjustment
    metrics_collector._adjust_sampling_rate()

    stats = metrics_collector.get_all_stats()
    sampling_info = stats.get("sampling", {})
    adaptive_info = sampling_info.get("adaptive", {})

    print(
        f"Sampling rate after high load: {metrics_collector.sampling_rate:.3f}"
    )
    print(f"Load score: {adaptive_info.get('current_load_score', 0):.3f}")
    print(
        f"Request volume: {adaptive_info.get('current_request_volume', 0):.1f} req/sec"
    )
    print(
        f"Total requests tracked: {len(metrics_collector._request_timestamps)}"
    )

    # Clean up memory
    del memory_blocks

    # Wait for CPU load to finish
    cpu_thread.join()

    # Test 3: Overhead measurement
    print("\n--- Test 3: Overhead Measurement ---")
    print("Measuring telemetry overhead...")

    # Measure baseline (no telemetry)
    start_time = time.time()
    for i in range(1000):
        # Simulate request processing without telemetry
        await asyncio.sleep(0.001)
    baseline_time = time.time() - start_time

    # Measure with telemetry
    start_time = time.time()
    for i in range(1000):
        with TracedSpan(f"overhead_test_{i}") as span:
            span.set_attribute("test", True)
            await asyncio.sleep(0.001)
    telemetry_time = time.time() - start_time

    overhead_percent = ((telemetry_time - baseline_time) / baseline_time) * 100
    print(".2f")
    print(".2f")
    print(".2f")

    # Validate overhead target
    if overhead_percent < 2.0:
        print("[PASS] Overhead target met (< 2%)")
    else:
        print("[FAIL] Overhead target exceeded (>= 2%)")

    # Final statistics
    print("\n--- Final Statistics ---")
    final_stats = metrics_collector.get_all_stats()
    print(f"Total requests recorded: {final_stats['total_requests']}")
    print(f"Successful requests: {final_stats['successful_requests']}")
    print(f"Failed requests: {final_stats['failed_requests']}")
    print(f"Final sampling rate: {metrics_collector.sampling_rate:.3f}")

    # Test completed - global metrics collector will continue running

    print("\nAdaptive sampling test completed!")


if __name__ == "__main__":
    asyncio.run(test_adaptive_sampling())
