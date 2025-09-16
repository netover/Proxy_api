"""
Performance benchmarks for cache behavior under memory pressure conditions.

This module provides detailed benchmarking for:
- Memory usage patterns under different cache configurations
- Performance degradation under memory pressure
- Eviction efficiency and impact on performance
- Recovery characteristics after memory pressure relief
"""

import asyncio
import gc
import os
import psutil
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, List, Any
import pytest

from src.core.model_cache import ModelCache
from src.core.smart_cache import SmartCache
from src.core.unified_cache import UnifiedCache
from src.models.model_info import ModelInfo


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    operation: str
    duration: float
    memory_usage_mb: float
    operations_per_second: float
    hit_rate: float = 0.0
    eviction_count: int = 0
    metadata: Dict[str, Any] = None


class CacheMemoryPressureBenchmark:
    """Benchmark cache performance under memory pressure."""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def benchmark_model_cache_memory_pressure(
        self, max_size: int = 100
    ) -> List[BenchmarkResult]:
        """Benchmark ModelCache under memory pressure."""
        results = []

        # Test different memory pressure levels
        pressure_levels = [0.5, 0.8, 1.0, 1.5]  # Multipliers for max_size

        for pressure in pressure_levels:
            cache = ModelCache(max_size=max_size, ttl=300)
            target_entries = int(max_size * pressure)

            # Fill cache to target level
            start_time = time.time()
            initial_memory = self.get_memory_usage()

            for i in range(target_entries):
                models = [
                    ModelInfo(
                        id=f"model-{i}",
                        object="model",
                        created=time.time(),
                        owned_by="benchmark",
                    )
                ]
                cache.set_models(
                    f"provider-{i}", f"https://provider-{i}.com", models
                )

            fill_time = time.time() - start_time
            fill_memory = self.get_memory_usage() - initial_memory

            # Benchmark access patterns under pressure
            access_start = time.time()
            hits = 0
            total_accesses = 200

            for i in range(total_accesses):
                key_idx = i % target_entries
                cached = cache.get_models(
                    f"provider-{key_idx}", f"https://provider-{key_idx}.com"
                )
                if cached:
                    hits += 1

            access_time = time.time() - access_start
            hit_rate = hits / total_accesses

            results.append(
                BenchmarkResult(
                    operation=f"model_cache_pressure_{pressure}x",
                    duration=access_time,
                    memory_usage_mb=fill_memory,
                    operations_per_second=total_accesses / access_time,
                    hit_rate=hit_rate,
                    metadata={
                        "cache_type": "ModelCache",
                        "max_size": max_size,
                        "target_entries": target_entries,
                        "pressure_multiplier": pressure,
                    },
                )
            )

        return results

    def benchmark_smart_cache_memory_limits(self) -> List[BenchmarkResult]:
        """Benchmark SmartCache with different memory limits."""
        results = []

        memory_limits = [1, 5, 10, 50]  # MB limits

        for limit_mb in memory_limits:
            cache = SmartCache(
                max_size=1000, max_memory_mb=limit_mb, default_ttl=300
            )

            # Create large entries to trigger memory limits
            large_data = {"data": "x" * 10000}  # ~10KB per entry
            entries_added = 0

            start_time = time.time()
            initial_memory = self.get_memory_usage()

            # Add entries until memory limit is approached
            for i in range(200):  # More than enough to trigger limits
                try:
                    # Simulate async set operation
                    entry = cache._cache.__class__(
                        key=f"large-{i}",
                        value=large_data,
                        timestamp=time.time(),
                        ttl=300,
                        size_bytes=len(str(large_data)),
                    )
                    cache._cache[f"large-{i}"] = entry
                    cache._cache.move_to_end(f"large-{i}")
                    entries_added += 1

                    # Check if we've hit memory limit
                    if (
                        sum(e.size_bytes for e in cache._cache.values())
                        / (1024 * 1024)
                        >= limit_mb
                    ):
                        break
                except Exception:
                    break

            # Enforce memory limits
            cache._enforce_memory_limit()

            final_memory = self.get_memory_usage()
            duration = time.time() - start_time

            results.append(
                BenchmarkResult(
                    operation=f"smart_cache_memory_{limit_mb}mb",
                    duration=duration,
                    memory_usage_mb=final_memory - initial_memory,
                    operations_per_second=(
                        entries_added / duration if duration > 0 else 0
                    ),
                    eviction_count=(
                        len(cache._cache) - entries_added
                        if len(cache._cache) < entries_added
                        else 0
                    ),
                    metadata={
                        "cache_type": "SmartCache",
                        "memory_limit_mb": limit_mb,
                        "entries_added": entries_added,
                        "final_cache_size": len(cache._cache),
                    },
                )
            )

        return results

    def benchmark_concurrent_memory_pressure(self) -> List[BenchmarkResult]:
        """Benchmark cache under concurrent memory pressure."""
        results = []

        cache = ModelCache(max_size=50, ttl=300)
        num_threads = [1, 2, 4, 8]

        for threads in num_threads:
            start_time = time.time()
            initial_memory = self.get_memory_usage()

            def worker_thread(thread_id: int):
                """Worker thread for concurrent operations."""
                for i in range(100):
                    key = f"thread-{thread_id}-item-{i}"
                    models = [
                        ModelInfo(
                            id=f"model-{key}",
                            object="model",
                            created=time.time(),
                            owned_by="concurrent_test",
                        )
                    ]
                    cache.set_models(key, f"https://{key}.com", models)

                    # Read operation
                    cache.get_models(key, f"https://{key}.com")

            # Run concurrent threads
            thread_list = []
            for i in range(threads):
                thread = threading.Thread(target=worker_thread, args=(i,))
                thread_list.append(thread)
                thread.start()

            for thread in thread_list:
                thread.join()

            duration = time.time() - start_time
            final_memory = self.get_memory_usage()

            total_operations = (
                threads * 200
            )  # 100 writes + 100 reads per thread

            results.append(
                BenchmarkResult(
                    operation=f"concurrent_memory_{threads}_threads",
                    duration=duration,
                    memory_usage_mb=final_memory - initial_memory,
                    operations_per_second=total_operations / duration,
                    metadata={
                        "cache_type": "ModelCache",
                        "thread_count": threads,
                        "total_operations": total_operations,
                        "final_cache_size": cache.get_stats()["size"],
                    },
                )
            )

        return results

    def benchmark_eviction_performance_impact(self) -> List[BenchmarkResult]:
        """Benchmark performance impact of frequent evictions."""
        results = []

        cache_sizes = [10, 50, 100, 500]

        for max_size in cache_sizes:
            cache = ModelCache(max_size=max_size, ttl=300)

            # Measure baseline performance
            baseline_times = []
            for i in range(50):
                models = [
                    ModelInfo(
                        id=f"baseline-{i}",
                        object="model",
                        created=time.time(),
                        owned_by="test",
                    )
                ]
                cache.set_models(
                    f"baseline-{i}", f"https://baseline-{i}.com", models
                )

                start = time.time()
                cache.get_models(f"baseline-{i}", f"https://baseline-{i}.com")
                baseline_times.append(time.time() - start)

            baseline_avg = statistics.mean(baseline_times)

            # Clear cache and test with frequent evictions
            cache.invalidate_all()

            eviction_times = []
            for i in range(max_size * 3):  # Exceed capacity multiple times
                models = [
                    ModelInfo(
                        id=f"eviction-{i}",
                        object="model",
                        created=time.time(),
                        owned_by="test",
                    )
                ]
                cache.set_models(
                    f"eviction-{i}", f"https://eviction-{i}.com", models
                )

                start = time.time()
                cached = cache.get_models(
                    f"eviction-{i}", f"https://eviction-{i}.com"
                )
                if cached:
                    eviction_times.append(time.time() - start)

            eviction_avg = (
                statistics.mean(eviction_times) if eviction_times else 0
            )

            results.append(
                BenchmarkResult(
                    operation=f"eviction_impact_size_{max_size}",
                    duration=eviction_avg,
                    memory_usage_mb=0,  # Not measuring memory here
                    operations_per_second=(
                        1 / eviction_avg if eviction_avg > 0 else 0
                    ),
                    metadata={
                        "cache_type": "ModelCache",
                        "max_size": max_size,
                        "baseline_avg_time": baseline_avg,
                        "eviction_avg_time": eviction_avg,
                        "performance_impact": (
                            (eviction_avg - baseline_avg) / baseline_avg
                            if baseline_avg > 0
                            else 0
                        ),
                    },
                )
            )

        return results

    def benchmark_memory_recovery_patterns(self) -> List[BenchmarkResult]:
        """Benchmark cache recovery after memory pressure relief."""
        results = []

        cache = ModelCache(max_size=20, ttl=300)

        # Phase 1: Create memory pressure
        pressure_start = time.time()
        for i in range(50):  # Exceed capacity significantly
            models = [
                ModelInfo(
                    id=f"pressure-{i}",
                    object="model",
                    created=time.time(),
                    owned_by="test",
                )
            ]
            cache.set_models(
                f"pressure-{i}", f"https://pressure-{i}.com", models
            )

        pressure_time = time.time() - pressure_start
        after_pressure_size = cache.get_stats()["size"]

        # Phase 2: Simulate memory pressure relief
        relief_start = time.time()
        for i in range(15):  # Remove some entries
            cache.invalidate(f"pressure-{i}", f"https://pressure-{i}.com")

        relief_time = time.time() - relief_start
        after_relief_size = cache.get_stats()["size"]

        # Phase 3: Test recovery performance
        recovery_start = time.time()
        recovery_operations = 30

        for i in range(recovery_operations):
            models = [
                ModelInfo(
                    id=f"recovery-{i}",
                    object="model",
                    created=time.time(),
                    owned_by="test",
                )
            ]
            cache.set_models(
                f"recovery-{i}", f"https://recovery-{i}.com", models
            )

            # Immediate read to test responsiveness
            cache.get_models(f"recovery-{i}", f"https://recovery-{i}.com")

        recovery_time = time.time() - recovery_start
        final_size = cache.get_stats()["size"]

        results.append(
            BenchmarkResult(
                operation="memory_recovery_pattern",
                duration=recovery_time,
                memory_usage_mb=0,  # Not measuring absolute memory
                operations_per_second=recovery_operations / recovery_time,
                metadata={
                    "cache_type": "ModelCache",
                    "pressure_phase_time": pressure_time,
                    "relief_phase_time": relief_time,
                    "recovery_phase_time": recovery_time,
                    "after_pressure_size": after_pressure_size,
                    "after_relief_size": after_relief_size,
                    "final_size": final_size,
                    "recovery_operations": recovery_operations,
                },
            )
        )

        return results

    def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all memory pressure benchmarks."""
        all_results = []

        print("Running ModelCache memory pressure benchmarks...")
        all_results.extend(self.benchmark_model_cache_memory_pressure())

        print("Running SmartCache memory limits benchmarks...")
        all_results.extend(self.benchmark_smart_cache_memory_limits())

        print("Running concurrent memory pressure benchmarks...")
        all_results.extend(self.benchmark_concurrent_memory_pressure())

        print("Running eviction performance impact benchmarks...")
        all_results.extend(self.benchmark_eviction_performance_impact())

        print("Running memory recovery pattern benchmarks...")
        all_results.extend(self.benchmark_memory_recovery_patterns())

        return all_results

    def print_summary(self, results: List[BenchmarkResult]):
        """Print benchmark results summary."""
        print("\n" + "=" * 80)
        print("CACHE MEMORY PRESSURE BENCHMARK RESULTS")
        print("=" * 80)

        for result in results:
            print(f"\nOperation: {result.operation}")
            print(f"  Duration: {result.duration:.4f}s")
            print(f"  Memory Usage: {result.memory_usage_mb:.2f} MB")
            print(f"  Operations/sec: {result.operations_per_second:.0f}")
            if result.hit_rate > 0:
                print(f"  Hit Rate: {result.hit_rate:.2%}")
            if result.eviction_count > 0:
                print(f"  Evictions: {result.eviction_count}")
            if result.metadata:
                for key, value in result.metadata.items():
                    print(f"  {key}: {value}")


def run_memory_pressure_benchmarks():
    """Main function to run memory pressure benchmarks."""
    benchmark = CacheMemoryPressureBenchmark()
    results = benchmark.run_all_benchmarks()
    benchmark.print_summary(results)
    return results


if __name__ == "__main__":
    results = run_memory_pressure_benchmarks()
