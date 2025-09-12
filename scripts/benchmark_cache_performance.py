#!/usr/bin/env python3
"""
Cache Performance Benchmark Script

This script benchmarks cache performance before and after migration to ensure
no performance degradation occurred during the consolidation process.

Benchmarks include:
- Cache hit/miss rates
- Get/set operation latency
- Memory usage patterns
- Concurrent operation performance
- Category-based performance

Usage:
    python scripts/benchmark_cache_performance.py [options]

Options:
    --baseline         Capture baseline performance metrics
    --benchmark        Run performance benchmark
    --compare          Compare with baseline metrics
    --concurrent       Test concurrent operations
    --load-test        Run load test with multiple scenarios
    --export-results   Export benchmark results to file
    --help             Show this help message

Environment Variables:
    CACHE_BENCHMARK_DURATION     Benchmark duration in seconds (default: 60)
    CACHE_BENCHMARK_CONCURRENCY  Number of concurrent operations (default: 10)
    CACHE_BENCHMARK_OPERATIONS   Number of operations per test (default: 10000)

Example:
    python scripts/benchmark_cache_performance.py --baseline
    python scripts/benchmark_cache_performance.py --benchmark --concurrent
    python scripts/benchmark_cache_performance.py --compare --export-results
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import statistics
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.consolidated_cache import get_consolidated_cache_manager
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    test_name: str
    duration: float
    operations: int
    throughput: float  # ops/sec
    latency_avg: float  # milliseconds
    latency_p50: float  # milliseconds
    latency_p95: float  # milliseconds
    latency_p99: float  # milliseconds
    errors: int
    metadata: Dict[str, Any]


class CachePerformanceBenchmark:
    """Benchmarks cache performance metrics"""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.duration = int(os.getenv('CACHE_BENCHMARK_DURATION', '60'))
        self.concurrency = int(os.getenv('CACHE_BENCHMARK_CONCURRENCY', '10'))
        self.operations = int(os.getenv('CACHE_BENCHMARK_OPERATIONS', '10000'))

        # Benchmark state
        self.baseline_results: Optional[Dict[str, Any]] = None
        self.benchmark_results: List[BenchmarkResult] = []

        # Setup logging
        logging.basicConfig(level=logging.INFO)

    async def run_benchmarks(self) -> Dict[str, Any]:
        """Run the complete benchmark suite"""
        logger.info("Starting cache performance benchmarks")

        start_time = time.time()

        try:
            # Get cache manager
            cache_manager = await get_consolidated_cache_manager()

            if self.args.baseline:
                logger.info("Capturing baseline performance metrics")
                self.baseline_results = await self._capture_baseline(cache_manager)

            elif self.args.benchmark:
                logger.info("Running performance benchmarks")
                await self._run_performance_benchmarks(cache_manager)

            elif self.args.compare:
                logger.info("Comparing with baseline metrics")
                await self._run_comparison_benchmarks(cache_manager)

            elif self.args.load_test:
                logger.info("Running load test")
                await self._run_load_test(cache_manager)

            else:
                # Run full benchmark suite
                logger.info("Running full benchmark suite")
                await self._run_full_benchmark_suite(cache_manager)

            # Generate report
            duration = time.time() - start_time
            report = self._generate_benchmark_report(duration)

            if self.args.export_results:
                self._export_results(report)

            logger.info(f"Benchmarks completed in {duration:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Benchmarks failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }

    async def _capture_baseline(self, cache_manager) -> Dict[str, Any]:
        """Capture baseline performance metrics"""
        logger.info("Capturing baseline metrics")

        baseline = {
            "timestamp": time.time(),
            "cache_stats": await cache_manager.get_stats(),
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": os.cpu_count()
            }
        }

        # Run basic performance test
        basic_result = await self._run_basic_performance_test(cache_manager)
        baseline["basic_performance"] = {
            "operations": basic_result.operations,
            "throughput": basic_result.throughput,
            "latency_avg": basic_result.latency_avg
        }

        return baseline

    async def _run_performance_benchmarks(self, cache_manager) -> None:
        """Run performance benchmarks"""
        logger.info("Running performance benchmarks")

        # Test 1: Basic operations
        result = await self._run_basic_performance_test(cache_manager)
        self.benchmark_results.append(result)

        # Test 2: Concurrent operations
        if self.args.concurrent:
            result = await self._run_concurrent_performance_test(cache_manager)
            self.benchmark_results.append(result)

        # Test 3: Category-based operations
        result = await self._run_category_performance_test(cache_manager)
        self.benchmark_results.append(result)

        # Test 4: Memory pressure test
        result = await self._run_memory_pressure_test(cache_manager)
        self.benchmark_results.append(result)

        # Test 5: Cache hit/miss patterns
        result = await self._run_hit_miss_pattern_test(cache_manager)
        self.benchmark_results.append(result)

    async def _run_basic_performance_test(self, cache_manager) -> BenchmarkResult:
        """Run basic cache performance test"""
        logger.info("Running basic performance test")

        latencies = []
        errors = 0
        operations = 0

        start_time = time.time()
        end_time = start_time + self.duration

        while time.time() < end_time and operations < self.operations:
            try:
                # Generate test key and value
                key = f"bench_key_{operations % 10000}"
                value = {"data": f"test_value_{operations}", "timestamp": time.time()}

                # Alternate between set and get operations
                op_start = time.time()

                if operations % 2 == 0:
                    # Set operation
                    success = await cache_manager.set(key, value)
                else:
                    # Get operation
                    result = await cache_manager.get(key)

                op_end = time.time()
                latencies.append((op_end - op_start) * 1000)  # Convert to milliseconds

                operations += 1

            except Exception as e:
                errors += 1
                logger.debug(f"Operation error: {e}")

        duration = time.time() - start_time
        throughput = operations / duration if duration > 0 else 0

        return BenchmarkResult(
            test_name="basic_performance",
            duration=duration,
            operations=operations,
            throughput=throughput,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0,
            errors=errors,
            metadata={"test_type": "basic_operations"}
        )

    async def _run_concurrent_performance_test(self, cache_manager) -> BenchmarkResult:
        """Run concurrent operations performance test"""
        logger.info("Running concurrent performance test")

        async def worker(worker_id: int, results: List[Dict[str, Any]]):
            """Worker function for concurrent operations"""
            worker_latencies = []
            worker_operations = 0
            worker_errors = 0

            for i in range(self.operations // self.concurrency):
                try:
                    key = f"concurrent_key_{worker_id}_{i}"
                    value = {"worker": worker_id, "operation": i, "timestamp": time.time()}

                    op_start = time.time()

                    # Alternate operations
                    if i % 2 == 0:
                        success = await cache_manager.set(key, value)
                    else:
                        result = await cache_manager.get(key)

                    op_end = time.time()
                    worker_latencies.append((op_end - op_start) * 1000)
                    worker_operations += 1

                except Exception as e:
                    worker_errors += 1

            results.append({
                "operations": worker_operations,
                "latencies": worker_latencies,
                "errors": worker_errors
            })

        # Run concurrent workers
        start_time = time.time()
        results = []
        tasks = [worker(i, results) for i in range(self.concurrency)]
        await asyncio.gather(*tasks)
        duration = time.time() - start_time

        # Aggregate results
        total_operations = sum(r["operations"] for r in results)
        all_latencies = [lat for r in results for lat in r["latencies"]]
        total_errors = sum(r["errors"] for r in results)

        throughput = total_operations / duration if duration > 0 else 0

        return BenchmarkResult(
            test_name="concurrent_performance",
            duration=duration,
            operations=total_operations,
            throughput=throughput,
            latency_avg=statistics.mean(all_latencies) if all_latencies else 0,
            latency_p50=statistics.median(all_latencies) if all_latencies else 0,
            latency_p95=statistics.quantiles(all_latencies, n=20)[18] if len(all_latencies) >= 20 else 0,
            latency_p99=statistics.quantiles(all_latencies, n=100)[98] if len(all_latencies) >= 100 else 0,
            errors=total_errors,
            metadata={
                "concurrency": self.concurrency,
                "test_type": "concurrent_operations"
            }
        )

    async def _run_category_performance_test(self, cache_manager) -> BenchmarkResult:
        """Run category-based performance test"""
        logger.info("Running category performance test")

        categories = ["models", "responses", "summaries", "default"]
        latencies = []
        errors = 0
        operations = 0

        start_time = time.time()
        end_time = start_time + self.duration

        while time.time() < end_time and operations < self.operations:
            try:
                category = categories[operations % len(categories)]
                key = f"category_key_{operations % 10000}"
                value = {"category": category, "data": f"value_{operations}", "timestamp": time.time()}

                op_start = time.time()

                if operations % 2 == 0:
                    success = await cache_manager.set(key, value, category=category)
                else:
                    result = await cache_manager.get(key, category=category)

                op_end = time.time()
                latencies.append((op_end - op_start) * 1000)

                operations += 1

            except Exception as e:
                errors += 1

        duration = time.time() - start_time
        throughput = operations / duration if duration > 0 else 0

        return BenchmarkResult(
            test_name="category_performance",
            duration=duration,
            operations=operations,
            throughput=throughput,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0,
            errors=errors,
            metadata={"categories": categories, "test_type": "category_operations"}
        )

    async def _run_memory_pressure_test(self, cache_manager) -> BenchmarkResult:
        """Run memory pressure performance test"""
        logger.info("Running memory pressure test")

        latencies = []
        errors = 0
        operations = 0

        # Create larger values to induce memory pressure
        large_value = {"data": "x" * 10000, "metadata": {"size": "large"}}

        start_time = time.time()
        end_time = start_time + self.duration

        while time.time() < end_time and operations < min(self.operations, 1000):  # Limit for memory test
            try:
                key = f"memory_key_{operations}"

                op_start = time.time()
                success = await cache_manager.set(key, large_value)
                op_end = time.time()

                latencies.append((op_end - op_start) * 1000)

                operations += 1

            except Exception as e:
                errors += 1

        duration = time.time() - start_time
        throughput = operations / duration if duration > 0 else 0

        # Get final memory stats
        final_stats = await cache_manager.get_stats()
        memory_usage = final_stats.get("memory_usage_mb", 0)

        return BenchmarkResult(
            test_name="memory_pressure",
            duration=duration,
            operations=operations,
            throughput=throughput,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0,
            errors=errors,
            metadata={
                "final_memory_usage_mb": memory_usage,
                "value_size_kb": len(json.dumps(large_value)) / 1024,
                "test_type": "memory_pressure"
            }
        )

    async def _run_hit_miss_pattern_test(self, cache_manager) -> BenchmarkResult:
        """Run cache hit/miss pattern test"""
        logger.info("Running hit/miss pattern test")

        latencies = []
        hit_count = 0
        miss_count = 0
        errors = 0
        operations = 0

        # Pre-populate some entries
        for i in range(1000):
            key = f"pattern_key_{i}"
            value = {"pattern": "test", "index": i}
            await cache_manager.set(key, value)

        start_time = time.time()
        end_time = start_time + self.duration

        while time.time() < end_time and operations < self.operations:
            try:
                # 70% hits, 30% misses pattern
                if operations % 10 < 7:
                    key = f"pattern_key_{operations % 1000}"  # Hit
                else:
                    key = f"pattern_key_{1000 + (operations % 1000)}"  # Miss

                op_start = time.time()
                result = await cache_manager.get(key)
                op_end = time.time()

                latencies.append((op_end - op_start) * 1000)

                if result is not None:
                    hit_count += 1
                else:
                    miss_count += 1

                operations += 1

            except Exception as e:
                errors += 1

        duration = time.time() - start_time
        throughput = operations / duration if duration > 0 else 0
        hit_rate = hit_count / (hit_count + miss_count) if (hit_count + miss_count) > 0 else 0

        return BenchmarkResult(
            test_name="hit_miss_pattern",
            duration=duration,
            operations=operations,
            throughput=throughput,
            latency_avg=statistics.mean(latencies) if latencies else 0,
            latency_p50=statistics.median(latencies) if latencies else 0,
            latency_p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else 0,
            latency_p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0,
            errors=errors,
            metadata={
                "hit_count": hit_count,
                "miss_count": miss_count,
                "hit_rate": hit_rate,
                "test_type": "hit_miss_pattern"
            }
        )

    async def _run_comparison_benchmarks(self, cache_manager) -> None:
        """Run benchmarks and compare with baseline"""
        logger.info("Running comparison benchmarks")

        # Load baseline if available
        baseline_file = Path(".cache/benchmarks/baseline.json")
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                self.baseline_results = json.load(f)

        # Run current benchmarks
        await self._run_performance_benchmarks(cache_manager)

        # Compare results
        if self.baseline_results:
            await self._compare_with_baseline()

    async def _run_load_test(self, cache_manager) -> None:
        """Run comprehensive load test"""
        logger.info("Running comprehensive load test")

        # Run multiple benchmark types
        await self._run_performance_benchmarks(cache_manager)

        # Additional stress test
        result = await self._run_stress_test(cache_manager)
        self.benchmark_results.append(result)

    async def _run_stress_test(self, cache_manager) -> BenchmarkResult:
        """Run stress test with high load"""
        logger.info("Running stress test")

        # Use higher concurrency for stress test
        stress_concurrency = self.concurrency * 2

        async def stress_worker(worker_id: int, results: List[Dict[str, Any]]):
            """Stress test worker"""
            worker_operations = 0
            worker_errors = 0

            for i in range(self.operations // stress_concurrency):
                try:
                    # Mix of operations
                    key = f"stress_key_{worker_id}_{i}"
                    value = {"worker": worker_id, "operation": i, "data": "x" * 100}

                    # Random operation mix
                    op_type = i % 4
                    if op_type == 0:
                        await cache_manager.set(key, value)
                    elif op_type == 1:
                        await cache_manager.get(key)
                    elif op_type == 2:
                        await cache_manager.set(key, value, category="stress")
                    else:
                        await cache_manager.get(key, category="stress")

                    worker_operations += 1

                except Exception as e:
                    worker_errors += 1

            results.append({
                "operations": worker_operations,
                "errors": worker_errors
            })

        start_time = time.time()
        results = []
        tasks = [stress_worker(i, results) for i in range(stress_concurrency)]
        await asyncio.gather(*tasks)
        duration = time.time() - start_time

        total_operations = sum(r["operations"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        throughput = total_operations / duration if duration > 0 else 0

        return BenchmarkResult(
            test_name="stress_test",
            duration=duration,
            operations=total_operations,
            throughput=throughput,
            latency_avg=0,  # Not measured in stress test
            latency_p50=0,
            latency_p95=0,
            latency_p99=0,
            errors=total_errors,
            metadata={
                "concurrency": stress_concurrency,
                "test_type": "stress_test"
            }
        )

    async def _run_full_benchmark_suite(self, cache_manager) -> None:
        """Run the complete benchmark suite"""
        logger.info("Running full benchmark suite")

        # Run all benchmark types
        await self._run_performance_benchmarks(cache_manager)

        # Load test
        if self.args.load_test:
            await self._run_load_test(cache_manager)

    async def _compare_with_baseline(self) -> None:
        """Compare current results with baseline"""
        if not self.baseline_results:
            return

        logger.info("Comparing results with baseline")

        # Compare basic performance
        baseline_perf = self.baseline_results.get("basic_performance", {})
        current_basic = next((r for r in self.benchmark_results if r.test_name == "basic_performance"), None)

        if current_basic and baseline_perf:
            throughput_change = ((current_basic.throughput - baseline_perf.get("throughput", 0)) /
                               baseline_perf.get("throughput", 1)) * 100

            if abs(throughput_change) > 10:  # 10% change threshold
                logger.warning(f"Throughput changed by {throughput_change:.1f}% from baseline")

    def _generate_benchmark_report(self, duration: float) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        report = {
            "status": "completed",
            "timestamp": time.time(),
            "total_duration": round(duration, 2),
            "configuration": {
                "duration": self.duration,
                "concurrency": self.concurrency,
                "operations": self.operations
            },
            "results": [
                {
                    "test_name": r.test_name,
                    "duration": round(r.duration, 3),
                    "operations": r.operations,
                    "throughput": round(r.throughput, 2),
                    "latency_avg": round(r.latency_avg, 3),
                    "latency_p50": round(r.latency_p50, 3),
                    "latency_p95": round(r.latency_p95, 3),
                    "latency_p99": round(r.latency_p99, 3),
                    "errors": r.errors,
                    "error_rate": round(r.errors / r.operations, 4) if r.operations > 0 else 0,
                    "metadata": r.metadata
                }
                for r in self.benchmark_results
            ]
        }

        # Calculate summary statistics
        if self.benchmark_results:
            total_throughput = sum(r.throughput for r in self.benchmark_results)
            avg_throughput = total_throughput / len(self.benchmark_results)
            total_errors = sum(r.errors for r in self.benchmark_results)

            report["summary"] = {
                "total_tests": len(self.benchmark_results),
                "average_throughput": round(avg_throughput, 2),
                "total_errors": total_errors,
                "tests_completed": len(self.benchmark_results)
            }

        return report

    def _export_results(self, report: Dict[str, Any]) -> None:
        """Export benchmark results to file"""
        # Create benchmark directory
        benchmark_dir = Path(".cache/benchmarks")
        benchmark_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        filepath = benchmark_dir / filename

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Benchmark results exported to {filepath}")

        # Save as latest
        latest_file = benchmark_dir / "latest_results.json"
        with open(latest_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Cache Performance Benchmark Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Capture baseline performance metrics"
    )

    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run performance benchmark"
    )

    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare with baseline metrics"
    )

    parser.add_argument(
        "--concurrent",
        action="store_true",
        help="Test concurrent operations"
    )

    parser.add_argument(
        "--load-test",
        action="store_true",
        help="Run load test with multiple scenarios"
    )

    parser.add_argument(
        "--export-results",
        action="store_true",
        help="Export benchmark results to file"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()

    # Run benchmarks
    benchmark = CachePerformanceBenchmark(args)
    results = await benchmark.run_benchmarks()

    # Output results
    print(json.dumps(results, indent=2, default=str))

    # Exit with appropriate code
    if results.get("status") == "completed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())