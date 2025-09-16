#!/usr/bin/env python3
"""
HTTP Client Throughput Benchmark
Compares maximum throughput between http_client.py (v1) vs http_client_v2.py (v2)
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, List, Any
import json
from concurrent.futures import ThreadPoolExecutor

# Import both HTTP clients
from src.core.http_client import OptimizedHTTPClient
from src.core.http_client_v2 import AdvancedHTTPClient

# Configure logging
logging.basicConfig(
    level=logging.ERROR
)  # Minimize logging for throughput tests
logger = logging.getLogger(__name__)


class ThroughputBenchmarkResult:
    """Container for throughput benchmark results"""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.response_times: List[float] = []
        self.start_time: float = 0
        self.end_time: float = 0
        self.peak_concurrent_requests: int = 0
        self.metrics: Dict[str, Any] = {}

    @property
    def total_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def requests_per_second(self) -> float:
        return (
            self.successful_requests / self.total_time
            if self.total_time > 0
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
    def median_response_time(self) -> float:
        return (
            statistics.median(self.response_times)
            if self.response_times
            else 0
        )

    @property
    def p95_response_time(self) -> float:
        if len(self.response_times) >= 20:
            return statistics.quantiles(self.response_times, n=20)[18]
        return max(self.response_times) if self.response_times else 0


async def benchmark_throughput():
    """Benchmark maximum throughput for both HTTP clients"""

    print("HTTP Client Throughput Benchmark")
    print("=" * 60)

    # Test configurations
    test_configs = [
        {
            "name": "Low Concurrency (10 concurrent)",
            "concurrent_requests": 10,
            "total_requests": 100,
            "duration": 30,
        },
        {
            "name": "Medium Concurrency (50 concurrent)",
            "concurrent_requests": 50,
            "total_requests": 500,
            "duration": 30,
        },
        {
            "name": "High Concurrency (100 concurrent)",
            "concurrent_requests": 100,
            "total_requests": 1000,
            "duration": 30,
        },
    ]

    test_url = "https://httpbin.org/get"
    print(f"Test URL: {test_url}")
    print()

    results = {}

    for config in test_configs:
        print(f"Testing Configuration: {config['name']}")
        print(f"  Concurrent Requests: {config['concurrent_requests']}")
        print(f"  Total Requests: {config['total_requests']}")
        print(f"  Duration: {config['duration']}s")
        print("-" * 50)

        # Test OptimizedHTTPClient (v1)
        print("  Testing OptimizedHTTPClient (v1)...")
        v1_result = await run_throughput_test(
            OptimizedHTTPClient, "OptimizedHTTPClient_v1", test_url, config
        )

        # Test AdvancedHTTPClient (v2)
        print("  Testing AdvancedHTTPClient (v2)...")
        v2_result = await run_throughput_test(
            AdvancedHTTPClient, "AdvancedHTTPClient_v2", test_url, config
        )

        results[config["name"]] = {
            "v1": v1_result,
            "v2": v2_result,
            "config": config,
        }

        # Print configuration results
        print(f"  Results for {config['name']}:")
        print(".1f")
        print(".1f")
        print(".1f")
        print(f"    V1 Success Rate: {v1_result.success_rate:.1f}%")
        print(f"    V2 Success Rate: {v2_result.success_rate:.1f}%")
        print(
            f"    V1 Avg Response Time: {v1_result.avg_response_time*1000:.2f}ms"
        )
        print(
            f"    V2 Avg Response Time: {v2_result.avg_response_time*1000:.2f}ms"
        )
        print(
            f"    V1 Median Response Time: {v1_result.median_response_time*1000:.2f}ms"
        )
        print(
            f"    V2 Median Response Time: {v2_result.median_response_time*1000:.2f}ms"
        )
        print(
            f"    V1 P95 Response Time: {v1_result.p95_response_time*1000:.2f}ms"
        )
        print(
            f"    V2 P95 Response Time: {v2_result.p95_response_time*1000:.2f}ms"
        )
        print()

    # Overall comparison
    print("=" * 60)
    print("THROUGHPUT BENCHMARK SUMMARY")
    print("=" * 60)

    # Calculate overall metrics
    total_v1_rps = sum(r["v1"].requests_per_second for r in results.values())
    total_v2_rps = sum(r["v2"].requests_per_second for r in results.values())
    num_configs = len(results)

    avg_v1_rps = total_v1_rps / num_configs if num_configs > 0 else 0
    avg_v2_rps = total_v2_rps / num_configs if num_configs > 0 else 0

    print(f"Average Requests/Second:")
    print(".1f")
    print(".1f")
    print(".1f")
    print()

    # Configuration breakdown
    print("Configuration Breakdown:")
    print("-" * 30)
    for config_name, config_results in results.items():
        v1_rps = config_results["v1"].requests_per_second
        v2_rps = config_results["v2"].requests_per_second
        improvement = ((v2_rps - v1_rps) / v1_rps * 100) if v1_rps > 0 else 0

        print(f"  {config_name}:")
        print(".1f")
        print(".1f")
        print("+6.1f")

    # Performance scaling analysis
    print("\nPerformance Scaling Analysis:")
    print("-" * 35)

    low_config = results.get("Low Concurrency (10 concurrent)")
    medium_config = results.get("Medium Concurrency (50 concurrent)")
    high_config = results.get("High Concurrency (100 concurrent)")

    if low_config and medium_config and high_config:
        print("V1 Scaling:")
        low_v1 = low_config["v1"].requests_per_second
        med_v1 = medium_config["v1"].requests_per_second
        high_v1 = high_config["v1"].requests_per_second

        print(".1f")
        print(".1f")
        print(".1f")

        print("V2 Scaling:")
        low_v2 = low_config["v2"].requests_per_second
        med_v2 = medium_config["v2"].requests_per_second
        high_v2 = high_config["v2"].requests_per_second

        print(".1f")
        print(".1f")
        print(".1f")

    # Resource efficiency analysis
    print("\nResource Efficiency Analysis:")
    print("-" * 35)

    for config_name, config_results in results.items():
        v1_result = config_results["v1"]
        v2_result = config_results["v2"]

        print(f"  {config_name}:")

        # Efficiency = requests per second per unit of response time
        v1_efficiency = (
            v1_result.requests_per_second / v1_result.avg_response_time
            if v1_result.avg_response_time > 0
            else 0
        )
        v2_efficiency = (
            v2_result.requests_per_second / v2_result.avg_response_time
            if v2_result.avg_response_time > 0
            else 0
        )

        print(".3f")
        print(".3f")
        print("+6.3f")

    # Detailed metrics
    print("\nDetailed Metrics by Configuration:")
    print("-" * 40)
    for config_name, config_results in results.items():
        print(f"\n{config_name}:")
        print(
            "  V1 Metrics:",
            json.dumps(config_results["v1"].metrics, indent=4, default=str),
        )
        print(
            "  V2 Metrics:",
            json.dumps(config_results["v2"].metrics, indent=4, default=str),
        )

    return results


async def run_throughput_test(
    client_class, client_name: str, url: str, config: Dict[str, Any]
) -> ThroughputBenchmarkResult:
    """Run throughput test for a specific client and configuration"""

    result = ThroughputBenchmarkResult(client_name)
    concurrent_requests = config["concurrent_requests"]
    total_requests = config["total_requests"]
    duration = config["duration"]

    # Initialize client with optimized settings for high throughput
    if client_class == OptimizedHTTPClient:
        client = client_class(
            max_keepalive_connections=concurrent_requests * 2,
            max_connections=concurrent_requests * 4,
            timeout=30.0,
            retry_attempts=1,  # Minimal retries for throughput tests
        )
    else:  # AdvancedHTTPClient
        client = client_class(
            provider_name="throughput_test",
            max_keepalive_connections=concurrent_requests * 2,
            max_connections=concurrent_requests * 4,
            timeout=30.0,
        )

    async with client:
        # Warm-up phase
        print("    Warm-up phase...")
        warmup_tasks = []
        for _ in range(min(10, concurrent_requests)):
            task = asyncio.create_task(
                make_request(client, url, result, is_warmup=True)
            )
            warmup_tasks.append(task)

        await asyncio.gather(*warmup_tasks)
        await asyncio.sleep(1)

        # Main test phase
        print("    Main test phase...")
        result.start_time = time.time()
        result.total_requests = 0
        result.successful_requests = 0
        result.failed_requests = 0
        result.response_times = []

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def limited_request():
            async with semaphore:
                await make_request(client, url, result, is_warmup=False)

        # Run requests for the specified duration
        tasks = []
        start_time = time.time()

        while (
            time.time() - start_time < duration
            and result.total_requests < total_requests
        ):
            if len(tasks) < concurrent_requests:
                task = asyncio.create_task(limited_request())
                tasks.append(task)

            # Clean up completed tasks
            tasks = [t for t in tasks if not t.done()]

            # Small yield to prevent blocking
            await asyncio.sleep(0.001)

        # Wait for remaining tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        result.end_time = time.time()

    # Get final metrics
    try:
        result.metrics = client.get_metrics()
    except Exception as e:
        result.metrics = {"error": str(e)}

    return result


async def make_request(
    client,
    url: str,
    result: ThroughputBenchmarkResult,
    is_warmup: bool = False,
):
    """Make a single HTTP request and record metrics"""
    start_time = time.time()

    try:
        response = await client.request("GET", url)
        async with response:
            if response.status_code == 200:
                if not is_warmup:
                    result.successful_requests += 1
            else:
                if not is_warmup:
                    result.failed_requests += 1
    except Exception as e:
        if not is_warmup:
            result.failed_requests += 1

    end_time = time.time()
    response_time = end_time - start_time

    if not is_warmup:
        result.total_requests += 1
        result.response_times.append(response_time)


if __name__ == "__main__":
    asyncio.run(benchmark_throughput())
