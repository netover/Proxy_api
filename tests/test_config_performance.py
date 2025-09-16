"""
Configuration Loading Performance Tests

Tests the performance improvements of the optimized configuration loader.
"""

import time
import asyncio
import statistics
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json
import sys
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from core.optimized_config import (
    OptimizedConfigLoader,
    load_critical_config,
    load_config_section,
    load_full_config,
    get_config_performance_stats,
)
from core.unified_config import ConfigManager
from core.app_config import load_config as load_app_config


class ConfigPerformanceTester:
    """Tests configuration loading performance"""

    def __init__(self, config_path: Path, iterations: int = 10):
        self.config_path = config_path
        self.iterations = iterations
        self.results = {}

    def time_function(self, func, *args, **kwargs) -> List[float]:
        """Time a function over multiple iterations"""
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds
        return times

    async def time_async_function(self, func, *args, **kwargs) -> List[float]:
        """Time an async function over multiple iterations"""
        times = []
        for _ in range(self.iterations):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds
        return times

    def test_legacy_yaml_loading(self) -> Dict[str, Any]:
        """Test legacy synchronous YAML loading"""

        def load_yaml():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)

        times = self.time_function(load_yaml)
        return {
            "method": "legacy_yaml",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    def test_legacy_config_manager(self) -> Dict[str, Any]:
        """Test legacy ConfigManager loading"""
        manager = ConfigManager(self.config_path)

        def load_config():
            return manager.load_config(force_reload=True)

        times = self.time_function(load_config)
        return {
            "method": "legacy_config_manager",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    def test_legacy_app_config(self) -> Dict[str, Any]:
        """Test legacy app config loading"""

        def load_app():
            return load_app_config()

        times = self.time_function(load_app)
        return {
            "method": "legacy_app_config",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    async def test_optimized_full_loading(self) -> Dict[str, Any]:
        """Test optimized full config loading"""
        times = await self.time_async_function(load_full_config)
        return {
            "method": "optimized_full",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    async def test_optimized_critical_loading(self) -> Dict[str, Any]:
        """Test optimized critical config loading"""
        times = await self.time_async_function(load_critical_config)
        return {
            "method": "optimized_critical",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    async def test_lazy_loading(self) -> Dict[str, Any]:
        """Test lazy loading of non-critical sections"""
        lazy_sections = [
            "telemetry",
            "chaos_engineering",
            "load_testing",
            "network_simulation",
        ]

        total_times = []
        for section in lazy_sections:
            times = await self.time_async_function(
                load_config_section, section
            )
            total_times.extend(times)

        return {
            "method": "lazy_loading",
            "sections_tested": lazy_sections,
            "times_ms": total_times,
            "avg_time_ms": statistics.mean(total_times),
            "min_time_ms": min(total_times),
            "max_time_ms": max(total_times),
            "std_dev_ms": (
                statistics.stdev(total_times) if len(total_times) > 1 else 0
            ),
        }

    async def test_cache_performance(self) -> Dict[str, Any]:
        """Test caching performance"""
        # First load to populate cache
        await load_full_config()

        # Then measure cached loads
        times = await self.time_async_function(load_full_config)

        return {
            "method": "cached_loading",
            "times_ms": times,
            "avg_time_ms": statistics.mean(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "std_dev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all performance tests"""
        print("Running configuration loading performance tests...")
        print(f"Config file: {self.config_path}")
        print(f"File size: {self.config_path.stat().st_size} bytes")
        print(f"Iterations per test: {self.iterations}")
        print("-" * 60)

        results = {}

        # Test legacy methods
        print("Testing legacy YAML loading...")
        results["legacy_yaml"] = self.test_legacy_yaml_loading()

        print("Testing legacy ConfigManager...")
        results["legacy_config_manager"] = self.test_legacy_config_manager()

        print("Testing legacy AppConfig...")
        results["legacy_app_config"] = self.test_legacy_app_config()

        # Test optimized methods
        print("Testing optimized full loading...")
        results["optimized_full"] = await self.test_optimized_full_loading()

        print("Testing optimized critical loading...")
        results["optimized_critical"] = (
            await self.test_optimized_critical_loading()
        )

        print("Testing lazy loading...")
        results["lazy_loading"] = await self.test_lazy_loading()

        print("Testing cached loading...")
        results["cached_loading"] = await self.test_cache_performance()

        # Get performance stats from optimized loader
        results["performance_stats"] = get_config_performance_stats()

        return results

    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\nPERFORMANCE TEST RESULTS")
        print("=" * 80)

        # Summary table
        print(
            f"{'Method':<30} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12} {'Std Dev':<12}"
        )
        print("-" * 80)

        for method, data in results.items():
            if method == "performance_stats":
                continue
            print(
                f"{method:<30} {data['avg_time_ms']:<12.2f} {data['min_time_ms']:<12.2f} {data['max_time_ms']:<12.2f} {data['std_dev_ms']:<12.2f}"
            )

        print("-" * 80)

        # Performance improvements
        if "legacy_config_manager" in results and "optimized_full" in results:
            legacy_avg = results["legacy_config_manager"]["avg_time_ms"]
            optimized_avg = results["optimized_full"]["avg_time_ms"]
            improvement = ((legacy_avg - optimized_avg) / legacy_avg) * 100

            print("\nPERFORMANCE IMPROVEMENT")
            print(f"Legacy average: {legacy_avg:.2f} ms")
            print(f"Optimized average: {optimized_avg:.2f} ms")
            print(f"Improvement: {improvement:.1f}%")

            if improvement >= 20:
                print("Target achieved: 20% improvement reached!")
            else:
                print("Target not met: Need more optimization")

        # Cache performance
        if "optimized_full" in results and "cached_loading" in results:
            first_load = results["optimized_full"]["avg_time_ms"]
            cached_load = results["cached_loading"]["avg_time_ms"]
            cache_improvement = ((first_load - cached_load) / first_load) * 100

            print("\nCACHE PERFORMANCE")
            print(f"First load: {first_load:.2f} ms")
            print(f"Cached load: {cached_load:.2f} ms")
            print(f"Cache improvement: {cache_improvement:.1f}%")

        # Lazy loading benefits
        if "lazy_loading" in results:
            lazy_avg = results["lazy_loading"]["avg_time_ms"]
            print("\nLAZY LOADING PERFORMANCE")
            print(f"Average lazy load time: {lazy_avg:.2f} ms")

        # Performance stats from optimized loader
        if "performance_stats" in results:
            stats = results["performance_stats"]
            print("\nOPTIMIZED LOADER STATS")
            print(f"Total loads: {stats['total_loads']}")
            print(f"Average duration: {stats['average_duration_ms']:.2f} ms")
            print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")
            print(f"Lazy loads: {stats['lazy_loads']}")


def main():
    """Main test function"""
    config_path = Path("config.yaml")

    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        return

    # Set dummy environment variables for testing
    import os

    os.environ["PROXY_API_OPENAI_API_KEY"] = "dummy_key_123"
    os.environ["PROXY_API_ANTHROPIC_API_KEY"] = "dummy_key_456"
    os.environ["PROXY_API_AZURE_OPENAI_KEY"] = "dummy_key_789"

    tester = ConfigPerformanceTester(config_path, iterations=5)
    results = asyncio.run(tester.run_all_tests())
    tester.print_results(results)


if __name__ == "__main__":
    main()
