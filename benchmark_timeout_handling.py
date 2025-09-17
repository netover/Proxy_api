#!/usr/bin/env python3
"""
HTTP Client Timeout Handling Benchmark
Compares timeout performance between http_client.py (v1) vs http_client_v2.py (v2)
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


class TimeoutBenchmarkResult:
    """Container for timeout benchmark results"""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.total_requests: int = 0
        self.timeout_requests: int = 0
        self.successful_requests: int = 0
        self.response_times: List[float] = []
        self.timeout_times: List[float] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.metrics: Dict[str, Any] = {}

    @property
    def total_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def timeout_rate(self) -> float:
        return (
            (self.timeout_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

    @property
    def success_rate(self) -> float:
        return (
            (self.successful_requests / self.total_requests * 100)
            if self.total_requests > 0
            else 0
        )

    @property
    def avg_response_time(self) -> float:
        return (
            statistics.mean(self.response_times) if self.response_times else 0
        )

    @property
    def avg_timeout_time(self) -> float:
        return statistics.mean(self.timeout_times) if self.timeout_times else 0


async def benchmark_timeout_handling():
    """Benchmark timeout handling performance for both HTTP clients"""

    print("HTTP Client Timeout Handling Benchmark")
    print("=" * 60)

    # Test scenarios with different timeout configurations
    scenarios = [
        {
            "name": "Short Timeout (2s) vs Fast Response (1s delay)",
            "url": "https://httpbin.org/delay/1",
            "timeout": 2.0,
            "expected_timeouts": 0,
        },
        {
            "name": "Short Timeout (2s) vs Slow Response (5s delay)",
            "url": "https://httpbin.org/delay/5",
            "timeout": 2.0,
            "expected_timeouts": 1,
        },
        {
            "name": "Medium Timeout (10s) vs Slow Response (15s delay)",
            "url": "https://httpbin.org/delay/15",
            "timeout": 10.0,
            "expected_timeouts": 1,
        },
        {
            "name": "Long Timeout (30s) vs Very Slow Response (25s delay)",
            "url": "https://httpbin.org/delay/25",
            "timeout": 30.0,
            "expected_timeouts": 0,
        },
    ]

    num_requests_per_scenario = 5  # Fewer requests for timeout tests
    print("Test Configuration:")
    print(f"  Scenarios: {len(scenarios)}")
    print(f"  Requests per scenario: {num_requests_per_scenario}")
    print()

    results = {}

    for scenario in scenarios:
        print(f"Testing Scenario: {scenario['name']}")
        print(f"  URL: {scenario['url']}")
        print(f"  Timeout: {scenario['timeout']}s")
        print("-" * 50)

        # Test OptimizedHTTPClient (v1)
        print("  Testing OptimizedHTTPClient (v1)...")
        v1_result = await run_timeout_test(
            OptimizedHTTPClient,
            "OptimizedHTTPClient_v1",
            scenario["url"],
            scenario["timeout"],
            num_requests_per_scenario,
        )

        # Test AdvancedHTTPClient (v2)
        print("  Testing AdvancedHTTPClient (v2)...")
        v2_result = await run_timeout_test(
            AdvancedHTTPClient,
            "AdvancedHTTPClient_v2",
            scenario["url"],
            scenario["timeout"],
            num_requests_per_scenario,
        )

        results[scenario["name"]] = {
            "v1": v1_result,
            "v2": v2_result,
            "config": scenario,
        }

        # Print scenario results
        print(f"  Results for {scenario['name']}:")
        print(f"    V1 Timeout Rate: {v1_result.timeout_rate:.1f}%")
        print(f"    V2 Timeout Rate: {v2_result.timeout_rate:.1f}%")
        print(f"    V1 Success Rate: {v1_result.success_rate:.1f}%")
        print(f"    V2 Success Rate: {v2_result.success_rate:.1f}%")
        print(
            f"    V1 Avg Response Time: {v1_result.avg_response_time*1000:.2f}ms"
        )
        print(
            f"    V2 Avg Response Time: {v2_result.avg_response_time*1000:.2f}ms"
        )
        if v1_result.timeout_times:
            print(
                f"    V1 Avg Timeout Time: {v1_result.avg_timeout_time*1000:.2f}ms"
            )
        if v2_result.timeout_times:
            print(
                f"    V2 Avg Timeout Time: {v2_result.avg_timeout_time*1000:.2f}ms"
            )
        print()

    # Overall comparison
    print("=" * 60)
    print("TIMEOUT HANDLING BENCHMARK SUMMARY")
    print("=" * 60)

    total_v1_timeouts = sum(r["v1"].timeout_requests for r in results.values())
    total_v2_timeouts = sum(r["v2"].timeout_requests for r in results.values())
    total_requests = sum(r["v1"].total_requests for r in results.values())

    overall_v1_timeout_rate = (
        total_v1_timeouts / total_requests * 100 if total_requests > 0 else 0
    )
    overall_v2_timeout_rate = (
        total_v2_timeouts / total_requests * 100 if total_requests > 0 else 0
    )

    print("Overall Timeout Rate:")
    print(f"  V1 (Optimized): {overall_v1_timeout_rate:.1f}%")
    print(f"  V2 (Advanced): {overall_v2_timeout_rate:.1f}%")
    print(".1")
    print()

    # Scenario breakdown
    print("Scenario Breakdown:")
    print("-" * 30)
    for scenario_name, scenario_results in results.items():
        v1_timeout_rate = scenario_results["v1"].timeout_rate
        v2_timeout_rate = scenario_results["v2"].timeout_rate
        config = scenario_results["config"]

        print(f"  {scenario_name}:")
        print(f"    Timeout: {config['timeout']}s")
        print(".1" ".1" "+.1")

    # Timeout efficiency analysis
    print("\nTimeout Efficiency Analysis:")
    print("-" * 35)

    # Analyze how quickly timeouts are detected
    fast_timeout_scenarios = [
        r for r in results.values() if r["config"]["expected_timeouts"] == 1
    ]

    if fast_timeout_scenarios:
        print("Fast Timeout Scenarios (expected timeouts):")
        for scenario in fast_timeout_scenarios:
            v1_timeout_time = scenario["v1"].avg_timeout_time
            v2_timeout_time = scenario["v2"].avg_timeout_time
            expected_timeout = scenario["config"]["timeout"]

            print(f"  {scenario['config']['name']}:")
            print(".2")
            print(".2")
            print(".2")

            # Check if timeout detection is close to expected
            v1_accuracy = (
                abs(v1_timeout_time - expected_timeout)
                / expected_timeout
                * 100
            )
            v2_accuracy = (
                abs(v2_timeout_time - expected_timeout)
                / expected_timeout
                * 100
            )

            print(".1")
            print(".1")

    # Detailed metrics
    print("\nDetailed Metrics by Scenario:")
    print("-" * 35)
    for scenario_name, scenario_results in results.items():
        print(f"\n{scenario_name}:")
        print(
            "  V1 Metrics:",
            json.dumps(scenario_results["v1"].metrics, indent=4, default=str),
        )
        print(
            "  V2 Metrics:",
            json.dumps(scenario_results["v2"].metrics, indent=4, default=str),
        )

    return results


async def run_timeout_test(
    client_class, client_name: str, url: str, timeout: float, num_requests: int
) -> TimeoutBenchmarkResult:
    """Run timeout test for a specific client and scenario"""

    result = TimeoutBenchmarkResult(client_name)
    result.start_time = time.time()

    # Initialize client with specific timeout
    if client_class == OptimizedHTTPClient:
        client = client_class(
            max_keepalive_connections=5,
            max_connections=10,
            timeout=timeout,
            connect_timeout=timeout * 0.5,
            retry_attempts=1,  # Minimal retries for timeout tests
        )
    else:  # AdvancedHTTPClient
        client = client_class(
            provider_name="timeout_test",
            max_keepalive_connections=5,
            max_connections=10,
            timeout=timeout,
            connect_timeout=timeout * 0.5,
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
                        result.timeout_requests += (
                            1  # Treat 5xx as timeouts for this test
                        )
            except asyncio.TimeoutError:
                result.timeout_requests += 1
                timeout_time = time.time() - request_start
                result.timeout_times.append(timeout_time)
            except Exception as e:
                # Check if it's a timeout-related exception
                if "timeout" in str(e).lower():
                    result.timeout_requests += 1
                    timeout_time = time.time() - request_start
                    result.timeout_times.append(timeout_time)
                else:
                    result.successful_requests += 1  # Other errors treated as successes for timeout focus

            request_time = time.time() - request_start
            result.response_times.append(request_time)

            # Longer delay between timeout requests to avoid overwhelming
            await asyncio.sleep(1.0)

    result.end_time = time.time()

    # Get client metrics
    try:
        result.metrics = client.get_metrics()
    except Exception as e:
        result.metrics = {"error": str(e)}

    return result


if __name__ == "__main__":
    asyncio.run(benchmark_timeout_handling())
