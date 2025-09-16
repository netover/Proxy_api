#!/usr/bin/env python3
"""
Comprehensive HTTP Client Connection Pooling Benchmark
Compares http_client.py (v1) vs http_client_v2.py (v2) performance
"""

import asyncio
import time
import logging
import statistics
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
import json

# Import both HTTP clients
from src.core.http_client import OptimizedHTTPClient
from src.core.http_client_v2 import AdvancedHTTPClient

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise during benchmarks
logger = logging.getLogger(__name__)


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, client_name: str):
        self.client_name = client_name
        self.response_times: List[float] = []
        self.errors: int = 0
        self.start_time: float = 0
        self.end_time: float = 0
        self.metrics: Dict[str, Any] = {}

    @property
    def total_time(self) -> float:
        return self.end_time - self.start_time

    @property
    def requests_per_second(self) -> float:
        if self.total_time > 0:
            return len(self.response_times) / self.total_time
        return 0

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
        if (
            len(self.response_times) >= 20
        ):  # Need enough samples for percentile
            return statistics.quantiles(self.response_times, n=20)[
                18
            ]  # 95th percentile
        return max(self.response_times) if self.response_times else 0


async def benchmark_connection_pooling():
    """Benchmark connection pooling performance for both HTTP clients"""

    print("HTTP Client Connection Pooling Benchmark")
    print("=" * 60)

    # Test configuration
    test_url = "https://httpbin.org/get"
    num_requests = 50
    concurrent_requests = 10
    test_duration = 30  # seconds for sustained load test

    print(f"Test Configuration:")
    print(f"  URL: {test_url}")
    print(f"  Total Requests: {num_requests}")
    print(f"  Concurrent Requests: {concurrent_requests}")
    print(f"  Sustained Load Duration: {test_duration}s")
    print()

    results = {}

    # Test OptimizedHTTPClient (v1)
    print("Testing OptimizedHTTPClient (v1)...")
    v1_result = await run_connection_pooling_test(
        OptimizedHTTPClient,
        "OptimizedHTTPClient_v1",
        test_url,
        num_requests,
        concurrent_requests,
        test_duration,
    )
    results["v1"] = v1_result

    # Reset for v2 test
    await asyncio.sleep(2)

    # Test AdvancedHTTPClient (v2)
    print("\nTesting AdvancedHTTPClient (v2)...")
    v2_result = await run_connection_pooling_test(
        AdvancedHTTPClient,
        "AdvancedHTTPClient_v2",
        test_url,
        num_requests,
        concurrent_requests,
        test_duration,
    )
    results["v2"] = v2_result

    # Print comparison results
    print("\n" + "=" * 60)
    print("CONNECTION POOLING BENCHMARK RESULTS")
    print("=" * 60)

    print(
        f"{'Metric':<25} {'V1 (Optimized)':<20} {'V2 (Advanced)':<20} {'Improvement':<15}"
    )
    print("-" * 80)

    # Response time metrics
    v1_avg = v1_result.avg_response_time * 1000
    v2_avg = v2_result.avg_response_time * 1000
    improvement = ((v1_avg - v2_avg) / v1_avg * 100) if v1_avg > 0 else 0

    print(".2f" ".2f" "+.1f")

    v1_median = v1_result.median_response_time * 1000
    v2_median = v2_result.median_response_time * 1000
    improvement = (
        ((v1_median - v2_median) / v1_median * 100) if v1_median > 0 else 0
    )

    print(".2f" ".2f" "+.1f")

    v1_p95 = v1_result.p95_response_time * 1000
    v2_p95 = v2_result.p95_response_time * 1000
    improvement = ((v1_p95 - v2_p95) / v1_p95 * 100) if v1_p95 > 0 else 0

    print(".2f" ".2f" "+.1f")

    # Throughput metrics
    print(".1f" ".1f" "+.1f")

    # Error rates
    v1_error_rate = (
        (v1_result.errors / num_requests * 100) if num_requests > 0 else 0
    )
    v2_error_rate = (
        (v2_result.errors / num_requests * 100) if num_requests > 0 else 0
    )
    improvement = v1_error_rate - v2_error_rate

    print(".2f" ".2f" "+.2f")

    # Connection pool metrics
    print("\nConnection Pool Metrics:")
    print("-" * 40)

    if "pool_info" in v1_result.metrics:
        pool_v1 = v1_result.metrics["pool_info"]
        print(
            f"V1 Pool Info: Total={pool_v1.get('total_connections', 0)}, "
            f"Available={pool_v1.get('available_connections', 0)}"
        )

    if "pool_info" in v2_result.metrics:
        pool_v2 = v2_result.metrics["pool_info"]
        print(
            f"V2 Pool Info: Total={pool_v2.get('total_connections', 0)}, "
            f"Available={pool_v2.get('available_connections', 0)}"
        )

    if "connection_reuse_rate" in v2_result.metrics:
        print(".1%")

    # Detailed metrics
    print("\nDetailed Metrics:")
    print("-" * 20)
    print("V1 Metrics:", json.dumps(v1_result.metrics, indent=2, default=str))
    print("V2 Metrics:", json.dumps(v2_result.metrics, indent=2, default=str))

    return results


async def run_connection_pooling_test(
    client_class,
    client_name: str,
    url: str,
    num_requests: int,
    concurrent_requests: int,
    test_duration: int,
) -> BenchmarkResult:
    """Run connection pooling test for a specific client"""

    result = BenchmarkResult(client_name)

    # Initialize client
    if client_class == OptimizedHTTPClient:
        client = client_class(
            max_keepalive_connections=20, max_connections=50, timeout=10.0
        )
    else:  # AdvancedHTTPClient
        client = client_class(
            provider_name="benchmark_test",
            max_keepalive_connections=20,
            max_connections=50,
            timeout=10.0,
        )

    async with client:
        # Warm-up phase
        print("  Warm-up phase...")
        for _ in range(5):
            try:
                response = await client.request("GET", url)
                await response.aclose()
            except Exception as e:
                print(f"    Warm-up error: {e}")

        await asyncio.sleep(1)

        # Sequential requests test
        print("  Sequential requests test...")
        result.start_time = time.time()

        for i in range(num_requests):
            try:
                start_req = time.time()
                response = await client.request("GET", url)
                async with response:
                    if response.status_code != 200:
                        result.errors += 1
                end_req = time.time()
                result.response_times.append(end_req - start_req)
            except Exception as e:
                result.errors += 1
                result.response_times.append(10.0)  # Timeout penalty

        result.end_time = time.time()

        # Concurrent requests test
        print("  Concurrent requests test...")
        concurrent_times = []

        async def concurrent_request(req_id: int):
            try:
                start_req = time.time()
                response = await client.request("GET", url)
                async with response:
                    if response.status_code != 200:
                        result.errors += 1
                end_req = time.time()
                concurrent_times.append(end_req - start_req)
            except Exception as e:
                result.errors += 1
                concurrent_times.append(10.0)

        # Run concurrent requests
        tasks = [concurrent_request(i) for i in range(concurrent_requests)]
        await asyncio.gather(*tasks)

        result.response_times.extend(concurrent_times)

        # Get client metrics
        try:
            result.metrics = client.get_metrics()
        except Exception as e:
            print(f"    Error getting metrics: {e}")
            result.metrics = {}

    return result


if __name__ == "__main__":
    asyncio.run(benchmark_connection_pooling())
