#!/usr/bin/env python3
"""
HTTP Client Retry Strategies Benchmark
Compares retry performance between http_client.py (v1) vs http_client_v2.py (v2)
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, List, Any
import json

# Import both HTTP clients
from src.core.http_client import OptimizedHTTPClient
from src.core.http_client_v2 import AdvancedHTTPClient

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class RetryBenchmarkResult:
    """Container for retry benchmark results"""
    def __init__(self, client_name: str):
        self.client_name = client_name
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.total_retries: int = 0
        self.response_times: List[float] = []
        self.retry_delays: List[float] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.metrics: Dict[str, Any] = {}

    @property
    def total_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        return (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0

    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0

    @property
    def avg_retry_delay(self) -> float:
        return statistics.mean(self.retry_delays) if self.retry_delays else 0

async def benchmark_retry_strategies():
    """Benchmark retry strategies performance for both HTTP clients"""

    print("HTTP Client Retry Strategies Benchmark")
    print("=" * 60)

    # Test scenarios
    scenarios = [
        {
            "name": "Normal Operation (200 OK)",
            "url": "https://httpbin.org/status/200",
            "expected_failures": 0
        },
        {
            "name": "Temporary Server Error (500)",
            "url": "https://httpbin.org/status/500",
            "expected_failures": 1  # Should retry and eventually succeed with delay
        },
        {
            "name": "Rate Limiting (429)",
            "url": "https://httpbin.org/status/429",
            "expected_failures": 1
        },
        {
            "name": "Timeout Simulation",
            "url": "https://httpbin.org/delay/15",  # 15 second delay
            "expected_failures": 1
        }
    ]

    num_requests_per_scenario = 10
    print(f"Test Configuration:")
    print(f"  Scenarios: {len(scenarios)}")
    print(f"  Requests per scenario: {num_requests_per_scenario}")
    print()

    results = {}

    for scenario in scenarios:
        print(f"Testing Scenario: {scenario['name']}")
        print("-" * 40)

        # Test OptimizedHTTPClient (v1)
        print("  Testing OptimizedHTTPClient (v1)...")
        v1_result = await run_retry_test(
            OptimizedHTTPClient,
            "OptimizedHTTPClient_v1",
            scenario["url"],
            num_requests_per_scenario
        )

        # Test AdvancedHTTPClient (v2)
        print("  Testing AdvancedHTTPClient (v2)...")
        v2_result = await run_retry_test(
            AdvancedHTTPClient,
            "AdvancedHTTPClient_v2",
            scenario["url"],
            num_requests_per_scenario
        )

        results[scenario["name"]] = {
            "v1": v1_result,
            "v2": v2_result
        }

        # Print scenario results
        print(f"  Results for {scenario['name']}:")
        print(f"    V1 Success Rate: {v1_result.success_rate:.1f}%")
        print(f"    V2 Success Rate: {v2_result.success_rate:.1f}%")
        print(f"    V1 Avg Response Time: {v1_result.avg_response_time*1000:.2f}ms")
        print(f"    V2 Avg Response Time: {v2_result.avg_response_time*1000:.2f}ms")
        print(f"    V1 Total Retries: {v1_result.total_retries}")
        print(f"    V2 Total Retries: {v2_result.total_retries}")
        print()

    # Overall comparison
    print("=" * 60)
    print("RETRY STRATEGIES BENCHMARK SUMMARY")
    print("=" * 60)

    total_v1_success = sum(r["v1"].successful_requests for r in results.values())
    total_v2_success = sum(r["v2"].successful_requests for r in results.values())
    total_requests = sum(r["v1"].total_requests for r in results.values())

    overall_v1_success_rate = total_v1_success / total_requests * 100 if total_requests > 0 else 0
    overall_v2_success_rate = total_v2_success / total_requests * 100 if total_requests > 0 else 0

    print(f"Overall Success Rate:")
    print(f"  V1 (Optimized): {overall_v1_success_rate:.1f}%")
    print(f"  V2 (Advanced): {overall_v2_success_rate:.1f}%")
    print(".1f")
    print()

    # Scenario breakdown
    print("Scenario Breakdown:")
    print("-" * 30)
    for scenario_name, scenario_results in results.items():
        v1_rate = scenario_results["v1"].success_rate
        v2_rate = scenario_results["v2"].success_rate
        improvement = v2_rate - v1_rate
        print(f"  {scenario_name}:")
        print(".1f"
              ".1f"
              "+.1f")

    # Detailed metrics
    print("\nDetailed Metrics by Scenario:")
    print("-" * 35)
    for scenario_name, scenario_results in results.items():
        print(f"\n{scenario_name}:")
        print("  V1 Metrics:", json.dumps(scenario_results["v1"].metrics, indent=4, default=str))
        print("  V2 Metrics:", json.dumps(scenario_results["v2"].metrics, indent=4, default=str))

    return results

async def run_retry_test(
    client_class,
    client_name: str,
    url: str,
    num_requests: int
) -> RetryBenchmarkResult:
    """Run retry test for a specific client and scenario"""

    result = RetryBenchmarkResult(client_name)
    result.start_time = time.time()

    # Initialize client
    if client_class == OptimizedHTTPClient:
        client = client_class(
            max_keepalive_connections=10,
            max_connections=20,
            timeout=10.0,
            retry_attempts=3,
            retry_backoff_factor=0.5
        )
    else:  # AdvancedHTTPClient
        client = client_class(
            provider_name="retry_test",
            max_keepalive_connections=10,
            max_connections=20,
            timeout=10.0
        )

    async with client:
        for i in range(num_requests):
            result.total_requests += 1
            request_start = time.time()

            try:
                response = await client.request("GET", url)
                async with response:
                    if response.status_code < 400:
                        result.successful_requests += 1
                    else:
                        result.failed_requests += 1
            except Exception as e:
                result.failed_requests += 1
                # Count retries based on exception type
                if "timeout" in str(e).lower() or "connect" in str(e).lower():
                    result.total_retries += 1  # Assume retry happened

            request_time = time.time() - request_start
            result.response_times.append(request_time)

            # Small delay between requests
            await asyncio.sleep(0.1)

    result.end_time = time.time()

    # Get client metrics
    try:
        result.metrics = client.get_metrics()
        # Add retry-specific metrics for v2
        if hasattr(client, 'get_retry_metrics'):
            result.metrics['retry_metrics'] = client.get_retry_metrics()
    except Exception as e:
        result.metrics = {"error": str(e)}

    return result

if __name__ == "__main__":
    asyncio.run(benchmark_retry_strategies())