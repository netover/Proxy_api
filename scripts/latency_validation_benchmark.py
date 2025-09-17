#!/usr/bin/env python3
"""
Latency Benchmarking Script for JSON Schema Validation
Measures startup time impact and runtime validation overhead
"""

import asyncio
import json
import os
import statistics
import sys
import time
import yaml
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the validation components
from src.core.config_schema import ConfigValidator, CONFIG_SCHEMA
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class ValidationBenchmark:
    """Benchmark class for JSON schema validation performance"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self.validator = ConfigValidator()
        self.test_configs = self._generate_test_configs()

    def _generate_test_configs(self) -> List[Dict[str, Any]]:
        """Generate test configurations of varying complexity"""
        base_config = {
            "app": {"name": "TestApp", "version": "1.0.0", "environment": "development"},
            "server": {"host": "127.0.0.1", "port": 8000, "debug": False, "reload": False},
            "auth": {"api_keys": ["test-key-123"]},
            "providers": [
                {
                    "name": "openai_test",
                    "type": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-3.5-turbo", "gpt-4"],
                    "enabled": True,
                    "priority": 1,
                    "timeout": 30,
                    "max_retries": 3,
                    "max_connections": 100,
                    "max_keepalive_connections": 10,
                    "keepalive_expiry": 30.0,
                    "retry_delay": 1.0
                }
            ]
        }

        configs = []

        # Light config (1 provider)
        configs.append(base_config.copy())

        # Medium config (5 providers)
        medium_config = base_config.copy()
        medium_config["providers"] = []
        for i in range(5):
            provider = base_config["providers"][0].copy()
            provider["name"] = f"provider_{i}"
            provider["priority"] = i + 1
            medium_config["providers"].append(provider)
        configs.append(medium_config)

        # Heavy config (20 providers)
        heavy_config = base_config.copy()
        heavy_config["providers"] = []
        for i in range(20):
            provider = base_config["providers"][0].copy()
            provider["name"] = f"provider_{i}"
            provider["priority"] = i + 1
            heavy_config["providers"].append(provider)
        configs.append(heavy_config)

        return configs

    def measure_startup_time_with_validation(self) -> Dict[str, float]:
        """Measure startup time with validation enabled"""
        results = {}

        for i, config in enumerate(self.test_configs):
            config_name = f"config_{['light', 'medium', 'heavy'][i]}"

            # Save test config
            test_config_path = Path(f"test_{config_name}.yaml")
            with open(test_config_path, 'w') as f:
                yaml.safe_dump(config, f)

            # Measure startup time
            start_time = time.time()
            try:
                validated_config = self.validator.validate_config_file(test_config_path)
                end_time = time.time()
                results[config_name] = end_time - start_time
                logger.info(".3")
            except Exception as e:
                logger.error(f"Validation failed for {config_name}: {e}")
                results[config_name] = float('inf')

            # Cleanup
            test_config_path.unlink(missing_ok=True)

        return results

    def measure_startup_time_without_validation(self) -> Dict[str, float]:
        """Measure startup time without validation (just YAML loading)"""
        results = {}

        for i, config in enumerate(self.test_configs):
            config_name = f"config_{['light', 'medium', 'heavy'][i]}"

            # Save test config
            test_config_path = Path(f"test_{config_name}.yaml")
            with open(test_config_path, 'w') as f:
                yaml.safe_dump(config, f)

            # Measure loading time without validation
            start_time = time.time()
            try:
                with open(test_config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                end_time = time.time()
                results[config_name] = end_time - start_time
                logger.info(".3")
            except Exception as e:
                logger.error(f"Loading failed for {config_name}: {e}")
                results[config_name] = float('inf')

            # Cleanup
            test_config_path.unlink(missing_ok=True)

        return results

    def measure_runtime_validation_overhead(self, iterations: int = 1000) -> Dict[str, List[float]]:
        """Measure runtime validation overhead under different scenarios"""
        scenarios = {
            "light_load": 10,    # 10 concurrent validations
            "medium_load": 50,   # 50 concurrent validations
            "heavy_load": 100    # 100 concurrent validations
        }

        results = {}

        for scenario_name, concurrency in scenarios.items():
            logger.info(f"Running {scenario_name} scenario with {concurrency} concurrent validations")

            latencies = []

            async def run_validation_batch():
                """Run a batch of validations"""
                tasks = []
                for _ in range(concurrency):
                    # Randomly select a config for variety
                    config = self.test_configs[len(self.test_configs) // 2]  # Use medium config
                    task = asyncio.get_event_loop().run_in_executor(
                        None, self._validate_config_sync, config
                    )
                    tasks.append(task)

                start_time = time.time()
                await asyncio.gather(*tasks)
                end_time = time.time()

                batch_latency = (end_time - start_time) / concurrency
                return [batch_latency] * concurrency

            # Run multiple batches
            for _ in range(iterations // concurrency):
                batch_latencies = asyncio.run(run_validation_batch())
                latencies.extend(batch_latencies)

            results[scenario_name] = latencies[:iterations]  # Trim to exact iterations

        return results

    def _validate_config_sync(self, config: Dict[str, Any]) -> None:
        """Synchronous validation wrapper"""
        try:
            self.validator.validate_config(config)
        except Exception as e:
            logger.warning(f"Validation error: {e}")

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        logger.info("Starting comprehensive JSON schema validation benchmark")

        results = {
            "timestamp": time.time(),
            "startup_with_validation": {},
            "startup_without_validation": {},
            "runtime_overhead": {},
            "summary": {}
        }

        # Measure startup times
        logger.info("Measuring startup times...")
        results["startup_with_validation"] = self.measure_startup_time_with_validation()
        results["startup_without_validation"] = self.measure_startup_time_without_validation()

        # Calculate startup overhead
        startup_overhead = {}
        for config_name in results["startup_with_validation"]:
            with_val = results["startup_with_validation"][config_name]
            without_val = results["startup_without_validation"][config_name]
            if without_val > 0:
                overhead = ((with_val - without_val) / without_val) * 100
                startup_overhead[config_name] = overhead
            else:
                startup_overhead[config_name] = float('inf')

        results["startup_overhead_percent"] = startup_overhead

        # Measure runtime overhead
        logger.info("Measuring runtime validation overhead...")
        runtime_results = self.measure_runtime_validation_overhead()

        # Calculate statistics for runtime results
        runtime_stats = {}
        for scenario, latencies in runtime_results.items():
            valid_latencies = [l for l in latencies if l != float('inf')]
            if valid_latencies:
                runtime_stats[scenario] = {
                    "mean": statistics.mean(valid_latencies),
                    "median": statistics.median(valid_latencies),
                    "p95": sorted(valid_latencies)[int(len(valid_latencies) * 0.95)],
                    "p99": sorted(valid_latencies)[int(len(valid_latencies) * 0.99)],
                    "min": min(valid_latencies),
                    "max": max(valid_latencies),
                    "count": len(valid_latencies)
                }
            else:
                runtime_stats[scenario] = {"error": "No valid measurements"}

        results["runtime_overhead"] = runtime_stats

        # Generate summary
        results["summary"] = self._generate_summary(results)

        logger.info("Benchmark completed")
        return results

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate benchmark summary"""
        summary = {
            "total_startup_overhead": {},
            "average_runtime_latency": {},
            "recommendations": []
        }

        # Startup overhead summary
        for config_name, overhead in results["startup_overhead_percent"].items():
            if overhead != float('in'):
                summary["total_startup_overhead"][config_name] = ".2f"
            else:
                summary["total_startup_overhead"][config_name] = "N/A"

        # Runtime latency summary
        for scenario, stats in results["runtime_overhead"].items():
            if "mean" in stats:
                summary["average_runtime_latency"][scenario] = ".4f"

        # Generate recommendations
        avg_startup_overhead = sum(
            v for v in results["startup_overhead_percent"].values()
            if v != float('in')
        ) / len([v for v in results["startup_overhead_percent"].values() if v != float('inf')])

        if avg_startup_overhead > 50:
            summary["recommendations"].append(
                ".1"
            )

        # Check runtime performance
        for scenario, stats in results["runtime_overhead"].items():
            if "p95" in stats and stats["p95"] > 0.1:  # 100ms threshold
                summary["recommendations"].append(
                    f"High P95 latency in {scenario} scenario ({stats['p95']:.4f}s). Consider optimizing schema or caching."
                )

        if not summary["recommendations"]:
            summary["recommendations"].append(
                "Validation performance is acceptable. No immediate optimizations needed."
            )

        return summary

    def save_results(self, results: Dict[str, Any], output_path: Path) -> None:
        """Save benchmark results to file"""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results saved to {output_path}")

def main():
    """Main benchmark execution"""
    import argparse

    parser = argparse.ArgumentParser(description="JSON Schema Validation Latency Benchmark")
    parser.add_argument("--config", type=Path, help="Path to config file")
    parser.add_argument("--output", type=Path, default=Path("validation_benchmark_results.json"),
                       help="Output file for results")
    parser.add_argument("--iterations", type=int, default=1000,
                       help="Number of runtime validation iterations")

    args = parser.parse_args()

    # Run benchmark
    benchmark = ValidationBenchmark(args.config)
    results = benchmark.run_comprehensive_benchmark()

    # Save results
    benchmark.save_results(results, args.output)

    # Print summary
    print("\n" + "="*60)
    print("JSON SCHEMA VALIDATION BENCHMARK RESULTS")
    print("="*60)

    print("\nSTARTUP TIME IMPACT:")
    for config, overhead in results["summary"]["total_startup_overhead"].items():
        print(f"  {config}: {overhead}")

    print("\nRUNTIME LATENCY (seconds):")
    for scenario, latency in results["summary"]["average_runtime_latency"].items():
        print(f"  {scenario}: {latency}")

    print("\nRECOMMENDATIONS:")
    for rec in results["summary"]["recommendations"]:
        print(f"  • {rec}")

    print(f"\nDetailed results saved to: {args.output}")

if __name__ == "__main__":
    main()