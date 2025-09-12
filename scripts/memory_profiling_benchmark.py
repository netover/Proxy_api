#!/usr/bin/env python3
"""
Memory Usage Profiling Benchmark for Enhanced Cache System

This script performs comprehensive memory profiling on the enhanced cache system
compared to the previous version, under different load scenarios.

Profiles memory overhead, potential leaks, and optimization opportunities.

Usage:
    python scripts/memory_profiling_benchmark.py [options]

Options:
    --light          Run light load scenario (1000 ops, 1 worker)
    --medium         Run medium load scenario (5000 ops, 5 workers)
    --heavy          Run heavy load scenario (10000 ops, 10 workers)
    --all            Run all load scenarios
    --enhanced       Profile enhanced cache system
    --previous       Profile previous cache system
    --both           Profile both systems (default)
    --export-results Export profiling results to file
    --help           Show this help message

Environment Variables:
    CACHE_MEMORY_DURATION     Benchmark duration in seconds (default: 30)
    CACHE_MEMORY_OPERATIONS   Number of operations per test (default: varies by load)

Example:
    python scripts/memory_profiling_benchmark.py --light --both --export-results
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from memory_profiler import profile, memory_usage
import gc
import psutil
import threading

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.consolidated_cache_enhanced import get_consolidated_cache_manager as get_enhanced_manager
from src.core.consolidated_cache import get_consolidated_cache_manager as get_previous_manager
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)


@dataclass
class MemoryProfileResult:
    """Result of a memory profiling test"""
    test_name: str
    cache_version: str
    load_scenario: str
    duration: float
    operations: int
    peak_memory_mb: float
    memory_increase_mb: float
    memory_leaks_mb: float
    gc_collections: int
    throughput: float
    metadata: Dict[str, Any]


class MemoryProfilingBenchmark:
    """Benchmarks memory usage for cache systems"""

    def __init__(self, args: argparse.Namespace):
        self.args = args

        # Load scenarios
        self.scenarios = {
            'light': {'operations': 1000, 'concurrency': 1, 'duration': 30},
            'medium': {'operations': 5000, 'concurrency': 5, 'duration': 60},
            'heavy': {'operations': 10000, 'concurrency': 10, 'duration': 120}
        }

        # Profiling state
        self.results: List[MemoryProfileResult] = []
        self.baseline_memory = 0

        # Setup logging
        logging.basicConfig(level=logging.INFO)

    async def run_profiling(self) -> Dict[str, Any]:
        """Run memory profiling benchmarks"""
        logger.info("Starting memory profiling benchmarks")

        start_time = time.time()

        try:
            # Determine which scenarios to run
            scenarios_to_run = []
            if self.args.light:
                scenarios_to_run.append('light')
            if self.args.medium:
                scenarios_to_run.append('medium')
            if self.args.heavy:
                scenarios_to_run.append('heavy')
            if self.args.all or not scenarios_to_run:
                scenarios_to_run = ['light', 'medium', 'heavy']

            # Determine which cache versions to profile
            versions_to_profile = []
            if self.args.enhanced:
                versions_to_profile.append('enhanced')
            if self.args.previous:
                versions_to_profile.append('previous')
            if self.args.both or not versions_to_profile:
                versions_to_profile = ['enhanced', 'previous']

            # Run profiling for each combination
            for scenario in scenarios_to_run:
                for version in versions_to_profile:
                    logger.info(f"Profiling {version} cache under {scenario} load")
                    result = await self._profile_cache_version(version, scenario)
                    self.results.append(result)

            # Generate report
            duration = time.time() - start_time
            report = self._generate_profiling_report(duration)

            if self.args.export_results:
                self._export_results(report)

            logger.info(f"Memory profiling completed in {duration:.2f}s")
            return report

        except Exception as e:
            logger.error(f"Profiling failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time
            }

    async def _profile_cache_version(self, version: str, scenario: str) -> MemoryProfileResult:
        """Profile a specific cache version under a load scenario"""
        config = self.scenarios[scenario]

        # Get cache manager
        if version == 'enhanced':
            cache_manager = await get_enhanced_manager()
        else:
            cache_manager = await get_previous_manager()

        # Setup memory profiling
        tracemalloc.start()
        gc.set_debug(gc.DEBUG_STATS)

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        self.baseline_memory = baseline_memory

        # Run the benchmark with memory profiling
        start_time = time.time()

        # Track memory usage during operations
        memory_samples = []
        initial_snapshot = tracemalloc.take_snapshot()

        # Run operations
        result = await self._run_load_scenario(cache_manager, config)

        # Take final snapshot
        final_snapshot = tracemalloc.take_snapshot()

        duration = time.time() - start_time

        # Get final memory stats
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - baseline_memory

        # Check for memory leaks using tracemalloc
        current, peak = tracemalloc.get_traced_memory()
        memory_leaks = peak / 1024 / 1024  # Convert to MB

        # Get memory usage from snapshots
        stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
        peak_memory_mb = max((stat.size / 1024 / 1024 for stat in stats), default=0)

        # Get GC stats
        gc_stats = gc.get_stats()
        gc_collections = sum(stat.get('collected', 0) for stat in gc_stats)

        # Cleanup
        tracemalloc.stop()
        gc.set_debug(0)

        # Calculate throughput
        throughput = result['operations'] / duration if duration > 0 else 0

        return MemoryProfileResult(
            test_name=f"{version}_{scenario}",
            cache_version=version,
            load_scenario=scenario,
            duration=duration,
            operations=result['operations'],
            peak_memory_mb=peak_memory_mb,
            memory_increase_mb=memory_increase,
            memory_leaks_mb=memory_leaks,
            gc_collections=gc_collections,
            throughput=throughput,
            metadata={
                "concurrency": config['concurrency'],
                "baseline_memory_mb": baseline_memory,
                "final_memory_mb": final_memory,
                "tracemalloc_current_mb": current / 1024 / 1024,
                "tracemalloc_peak_mb": peak / 1024 / 1024,
                "gc_stats": gc.get_stats(),
                "memory_usage_samples": memory_samples
            }
        )

    async def _run_load_scenario(self, cache_manager, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the actual load scenario operations"""
        operations_completed = 0
        errors = 0

        async def worker(worker_id: int):
            nonlocal operations_completed, errors
            ops_per_worker = config['operations'] // config['concurrency']

            for i in range(ops_per_worker):
                try:
                    # Generate test data
                    key = f"mem_test_key_{worker_id}_{i}"
                    value = {
                        "worker": worker_id,
                        "operation": i,
                        "data": "x" * 100,  # 100 bytes of data
                        "timestamp": time.time()
                    }

                    # Mix of operations: 60% sets, 40% gets
                    if i % 5 < 3:
                        # Set operation
                        await cache_manager.set(key, value, category="memory_test")
                    else:
                        # Get operation (may miss)
                        await cache_manager.get(key, category="memory_test")

                    operations_completed += 1

                except Exception as e:
                    errors += 1
                    logger.debug(f"Operation error: {e}")

        # Run concurrent workers
        tasks = [worker(i) for i in range(config['concurrency'])]
        await asyncio.gather(*tasks)

        return {
            "operations": operations_completed,
            "errors": errors
        }

    def _generate_profiling_report(self, duration: float) -> Dict[str, Any]:
        """Generate comprehensive profiling report"""
        report = {
            "status": "completed",
            "timestamp": time.time(),
            "total_duration": round(duration, 2),
            "scenarios_tested": list(set(r.load_scenario for r in self.results)),
            "versions_tested": list(set(r.cache_version for r in self.results)),
            "results": [
                {
                    "test_name": r.test_name,
                    "cache_version": r.cache_version,
                    "load_scenario": r.load_scenario,
                    "duration": round(r.duration, 3),
                    "operations": r.operations,
                    "peak_memory_mb": round(r.peak_memory_mb, 2),
                    "memory_increase_mb": round(r.memory_increase_mb, 2),
                    "memory_leaks_mb": round(r.memory_leaks_mb, 2),
                    "gc_collections": r.gc_collections,
                    "throughput": round(r.throughput, 2),
                    "memory_per_operation_kb": round((r.memory_increase_mb * 1024) / r.operations, 2) if r.operations > 0 else 0,
                    "metadata": r.metadata
                }
                for r in self.results
            ]
        }

        # Calculate comparisons between versions
        if len(set(r.cache_version for r in self.results)) > 1:
            report["comparisons"] = self._calculate_version_comparisons()

        # Calculate summary statistics
        if self.results:
            report["summary"] = {
                "total_tests": len(self.results),
                "average_memory_increase_mb": round(sum(r.memory_increase_mb for r in self.results) / len(self.results), 2),
                "max_memory_leaks_mb": round(max(r.memory_leaks_mb for r in self.results), 2),
                "total_gc_collections": sum(r.gc_collections for r in self.results)
            }

        return report

    def _calculate_version_comparisons(self) -> Dict[str, Any]:
        """Calculate comparisons between cache versions"""
        comparisons = {}

        # Group results by scenario
        scenario_groups = {}
        for result in self.results:
            key = result.load_scenario
            if key not in scenario_groups:
                scenario_groups[key] = {}
            scenario_groups[key][result.cache_version] = result

        # Compare each scenario
        for scenario, versions in scenario_groups.items():
            if 'enhanced' in versions and 'previous' in versions:
                enhanced = versions['enhanced']
                previous = versions['previous']

                memory_overhead = enhanced.memory_increase_mb - previous.memory_increase_mb
                memory_overhead_percent = (memory_overhead / previous.memory_increase_mb) * 100 if previous.memory_increase_mb > 0 else 0

                throughput_change = enhanced.throughput - previous.throughput
                throughput_change_percent = (throughput_change / previous.throughput) * 100 if previous.throughput > 0 else 0

                comparisons[scenario] = {
                    "memory_overhead_mb": round(memory_overhead, 2),
                    "memory_overhead_percent": round(memory_overhead_percent, 2),
                    "throughput_change_ops_sec": round(throughput_change, 2),
                    "throughput_change_percent": round(throughput_change_percent, 2),
                    "leak_difference_mb": round(enhanced.memory_leaks_mb - previous.memory_leaks_mb, 2),
                    "gc_difference": enhanced.gc_collections - previous.gc_collections,
                    "meets_target": abs(memory_overhead_percent) <= 10  # 10% target
                }

        return comparisons

    def _export_results(self, report: Dict[str, Any]) -> None:
        """Export profiling results to file"""
        # Create profiling directory
        profiling_dir = Path(".cache/profiling")
        profiling_dir.mkdir(parents=True, exist_ok=True)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"memory_profiling_results_{timestamp}.json"
        filepath = profiling_dir / filename

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Memory profiling results exported to {filepath}")

        # Save as latest
        latest_file = profiling_dir / "latest_memory_profiling.json"
        with open(latest_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Memory Profiling Benchmark for Cache Systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Load scenarios
    parser.add_argument(
        "--light",
        action="store_true",
        help="Run light load scenario (1000 ops, 1 worker)"
    )

    parser.add_argument(
        "--medium",
        action="store_true",
        help="Run medium load scenario (5000 ops, 5 workers)"
    )

    parser.add_argument(
        "--heavy",
        action="store_true",
        help="Run heavy load scenario (10000 ops, 10 workers)"
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all load scenarios"
    )

    # Cache versions
    parser.add_argument(
        "--enhanced",
        action="store_true",
        help="Profile enhanced cache system"
    )

    parser.add_argument(
        "--previous",
        action="store_true",
        help="Profile previous cache system"
    )

    parser.add_argument(
        "--both",
        action="store_true",
        help="Profile both cache systems (default)"
    )

    parser.add_argument(
        "--export-results",
        action="store_true",
        help="Export profiling results to file"
    )

    return parser.parse_args()


async def main():
    """Main entry point"""
    args = parse_arguments()

    # Run profiling
    benchmark = MemoryProfilingBenchmark(args)
    results = await benchmark.run_profiling()

    # Output results
    print(json.dumps(results, indent=2, default=str))

    # Exit with appropriate code
    if results.get("status") == "completed":
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())