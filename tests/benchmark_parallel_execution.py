"""
Performance Benchmark Suite for Parallel Execution System
Validates 60%+ latency reduction and throughput improvements
"""

import asyncio
import time
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import json
import os

from src.core.parallel_fallback import parallel_fallback_engine, ParallelExecutionMode
from src.core.provider_discovery import provider_discovery
from src.core.circuit_breaker_pool import circuit_breaker_pool
from src.core.load_balancer import load_balancer


@dataclass
class BenchmarkResult:
    """Result of a benchmark test"""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_time: float
    avg_latency: float
    p50_latency: float
    p95_latency: float
    p99_latency: float
    throughput_rps: float
    error_rate: float
    metadata: Dict[str, Any]


class MockBenchmarkProvider:
    """Benchmark provider with configurable performance characteristics"""

    def __init__(self, name: str, latency_ms: float, failure_rate: float = 0.0):
        self.name = name
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate
        self.requests_served = 0

    async def execute_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        self.requests_served += 1

        # Simulate failure
        if self.failure_rate > 0 and (self.requests_served % int(1/self.failure_rate)) == 0:
            await asyncio.sleep(self.latency_ms / 1000)
            raise Exception(f"Benchmark failure in {self.name}")

        # Simulate processing time
        await asyncio.sleep(self.latency_ms / 1000)

        return {
            "choices": [{"message": {"content": f"Benchmark response from {self.name}"}}],
            "usage": {"total_tokens": 100}
        }


class ParallelExecutionBenchmark:
    """Comprehensive benchmark suite for parallel execution"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.test_providers = {
            "fast_provider": MockBenchmarkProvider("fast_provider", latency_ms=200, failure_rate=0.02),
            "medium_provider": MockBenchmarkProvider("medium_provider", latency_ms=500, failure_rate=0.05),
            "slow_provider": MockBenchmarkProvider("slow_provider", latency_ms=1200, failure_rate=0.10),
            "unreliable_provider": MockBenchmarkProvider("unreliable_provider", latency_ms=300, failure_rate=0.50)
        }

    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run complete benchmark suite comparing sequential vs parallel execution"""
        print("🚀 Starting Parallel Execution Benchmark Suite")
        print("=" * 60)

        # Setup test environment
        await self._setup_benchmark_environment()

        # Run individual benchmarks
        await self._benchmark_sequential_vs_parallel()
        await self._benchmark_scalability_under_load()
        await self._benchmark_failure_resilience()
        await self._benchmark_provider_selection_optimization()

        # Generate comprehensive report
        report = self._generate_benchmark_report()

        # Save results
        self._save_benchmark_results(report)

        return report

    async def _setup_benchmark_environment(self):
        """Setup benchmark environment"""
        print("📋 Setting up benchmark environment...")

        # Reset all components
        await provider_discovery.reset_provider_metrics()
        await circuit_breaker_pool.shutdown()
        await load_balancer.shutdown()

        # Pre-warm the system
        print("🔥 Warming up system...")
        await self._warm_up_system()

        print("✅ Benchmark environment ready")

    async def _warm_up_system(self):
        """Warm up the system with initial requests"""
        request_data = {"messages": [{"role": "user", "content": "Warmup"}]}

        with self._mock_providers_context():
            for _ in range(10):
                await parallel_fallback_engine.execute_parallel(
                    model="gpt-3.5-turbo",
                    request_data=request_data,
                    execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                    timeout=5.0
                )

    async def _benchmark_sequential_vs_parallel(self):
        """Benchmark sequential vs parallel execution performance"""
        print("\n🔬 Benchmarking Sequential vs Parallel Execution")

        request_data = {"messages": [{"role": "user", "content": "Performance test"}]}
        num_requests = 50

        # Test sequential execution (simulated)
        print("  📊 Testing sequential execution...")
        sequential_latencies = await self._run_sequential_simulation(num_requests, request_data)
        sequential_result = self._analyze_latencies("sequential", sequential_latencies, num_requests)

        # Test parallel execution
        print("  📊 Testing parallel execution...")
        parallel_latencies = await self._run_parallel_execution(num_requests, request_data)
        parallel_result = self._analyze_latencies("parallel", parallel_latencies, num_requests)

        # Calculate improvement
        improvement_pct = ((sequential_result.avg_latency - parallel_result.avg_latency) /
                          sequential_result.avg_latency) * 100

        print(f"  📈 Latency Improvement: {improvement_pct:.1f}%")
        print(f"  ⚡ Sequential P95: {sequential_result.p95_latency:.1f}ms")
        print(f"  ⚡ Parallel P95: {parallel_result.p95_latency:.1f}ms")
        # Validate target achievement
        if improvement_pct >= 60:
            print("  ✅ TARGET ACHIEVED: 60%+ latency reduction")
        else:
            print("  ❌ Target not met - needs optimization")

        self.results.extend([sequential_result, parallel_result])

    async def _run_sequential_simulation(self, num_requests: int, request_data: Dict) -> List[float]:
        """Simulate sequential execution (calling providers one by one)"""
        latencies = []

        with self._mock_providers_context():
            for _ in range(num_requests):
                start_time = time.time()

                # Simulate sequential fallback (try fast, then medium, then slow)
                success = False
                for provider_name in ["fast_provider", "medium_provider", "slow_provider"]:
                    try:
                        provider = self.test_providers[provider_name]
                        await provider.execute_request(request_data)
                        success = True
                        break
                    except (Exception, asyncio.TimeoutError, ValueError) as e:
                        print(f"Provider {provider_name} failed: {e}")
                        continue

                if not success:
                    # Use unreliable as last resort
                    try:
                        await self.test_providers["unreliable_provider"].execute_request(request_data)
                    except (Exception, asyncio.TimeoutError, ValueError) as e:
                        print(f"Unreliable provider failed as last resort: {e}")
                        pass

                latencies.append((time.time() - start_time) * 1000)

        return latencies

    async def _run_parallel_execution(self, num_requests: int, request_data: Dict) -> List[float]:
        """Run parallel execution benchmark"""
        latencies = []

        with self._mock_providers_context():
            tasks = []
            for _ in range(num_requests):
                task = asyncio.create_task(
                    parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                        timeout=3.0,
                        max_providers=4
                    )
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, dict) and result.get('success'):
                    latencies.append(result.get('latency_ms', 3000))
                else:
                    latencies.append(3000)  # Timeout penalty

        return latencies

    async def _benchmark_scalability_under_load(self):
        """Benchmark scalability under high concurrent load"""
        print("\n🔬 Benchmarking Scalability Under Load")

        request_data = {"messages": [{"role": "user", "content": "Load test"}]}
        concurrent_levels = [10, 50, 100, 200]

        for concurrent in concurrent_levels:
            print(f"  📊 Testing {concurrent} concurrent requests...")

            latencies = await self._run_high_concurrency_test(concurrent, request_data)
            result = self._analyze_latencies(f"concurrent_{concurrent}", latencies, concurrent)

            print(f"  📊 Throughput: {result.throughput_rps:.0f} req/s")
            # Check throughput target (500+ req/s)
            if result.throughput_rps >= 500:
                print("  ✅ TARGET ACHIEVED: 500+ req/s throughput")
            elif result.throughput_rps >= 200:
                print("  ⚠️  Moderate throughput - room for optimization")

            self.results.append(result)

    async def _run_high_concurrency_test(self, num_concurrent: int, request_data: Dict) -> List[float]:
        """Run high concurrency test"""
        latencies = []

        with self._mock_providers_context():
            start_time = time.time()

            tasks = []
            for _ in range(num_concurrent):
                task = asyncio.create_task(
                    parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=ParallelExecutionMode.FIRST_SUCCESS,
                        timeout=5.0
                    )
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            for result in results:
                if isinstance(result, dict):
                    latencies.append(result.get('latency_ms', 5000))
                else:
                    latencies.append(5000)

        return latencies

    async def _benchmark_failure_resilience(self):
        """Benchmark system resilience under failure conditions"""
        print("\n🔬 Benchmarking Failure Resilience")

        # Increase failure rates to simulate degraded conditions
        self.test_providers["fast_provider"].failure_rate = 0.20
        self.test_providers["medium_provider"].failure_rate = 0.40

        request_data = {"messages": [{"role": "user", "content": "Failure resilience test"}]}
        num_requests = 100

        print("  📊 Testing under failure conditions...")
        latencies = await self._run_parallel_execution(num_requests, request_data)
        result = self._analyze_latencies("failure_resilience", latencies, num_requests)

        error_rate = result.error_rate * 100
        print(f"  📊 Error Rate: {error_rate:.1f}%")
        # Check error rate target (< 0.5%)
        if error_rate < 0.5:
            print("  ✅ TARGET ACHIEVED: <0.5% error rate")
        elif error_rate < 2.0:
            print("  ⚠️  Acceptable error rate - minor optimization needed")
        else:
            print("  ❌ High error rate - needs attention")

        self.results.append(result)

        # Reset failure rates
        self.test_providers["fast_provider"].failure_rate = 0.02
        self.test_providers["medium_provider"].failure_rate = 0.05

    async def _benchmark_provider_selection_optimization(self):
        """Benchmark provider selection optimization"""
        print("\n🔬 Benchmarking Provider Selection Optimization")

        request_data = {"messages": [{"role": "user", "content": "Selection test"]]}
        num_requests = 30

        # Run with different provider selection strategies
        strategies = [
            ("adaptive", ParallelExecutionMode.FIRST_SUCCESS),
            ("load_balanced", ParallelExecutionMode.LOAD_BALANCED)
        ]

        for strategy_name, mode in strategies:
            print(f"  📊 Testing {strategy_name} selection...")

            latencies = []
            with self._mock_providers_context():
                for _ in range(num_requests):
                    result = await parallel_fallback_engine.execute_parallel(
                        model="gpt-3.5-turbo",
                        request_data=request_data,
                        execution_mode=mode,
                        timeout=3.0
                    )
                    if result.success:
                        latencies.append(result.latency_ms)
                    else:
                        latencies.append(3000)

            result = self._analyze_latencies(f"selection_{strategy_name}", latencies, num_requests)
            self.results.append(result)

            print(f"  📊 Avg Latency: {result.avg_latency:.1f}ms")
    def _analyze_latencies(self, test_name: str, latencies: List[float], total_requests: int) -> BenchmarkResult:
        """Analyze latency measurements and create benchmark result"""
        if not latencies:
            return BenchmarkResult(
                test_name=test_name,
                total_requests=total_requests,
                successful_requests=0,
                failed_requests=total_requests,
                total_time=0,
                avg_latency=0,
                p50_latency=0,
                p95_latency=0,
                p99_latency=0,
                throughput_rps=0,
                error_rate=1.0,
                metadata={}
            )

        sorted_latencies = sorted(latencies)
        successful_requests = len([l for l in latencies if l < 3000])  # Under timeout threshold
        failed_requests = total_requests - successful_requests

        total_time = sum(latencies) / 1000  # Convert to seconds
        avg_latency = statistics.mean(latencies) if latencies else 0
        p50_latency = statistics.median(sorted_latencies) if sorted_latencies else 0
        p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)] if len(sorted_latencies) > 1 else p50_latency
        p99_latency = sorted_latencies[int(len(sorted_latencies) * 0.99)] if len(sorted_latencies) > 1 else p50_latency

        throughput_rps = successful_requests / (total_time / total_requests) if total_time > 0 else 0
        error_rate = failed_requests / total_requests

        return BenchmarkResult(
            test_name=test_name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_time=total_time,
            avg_latency=avg_latency,
            p50_latency=p50_latency,
            p95_latency=p95_latency,
            p99_latency=p99_latency,
            throughput_rps=throughput_rps,
            error_rate=error_rate,
            metadata={"latencies": latencies[:10]}  # Sample first 10 latencies
        )

    def _generate_benchmark_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        print("\n📊 Generating Benchmark Report")

        report = {
            "timestamp": time.time(),
            "summary": {
                "total_tests": len(self.results),
                "overall_success_rate": 0.0,
                "best_p95_latency": float('inf'),
                "best_throughput": 0.0,
                "targets_achieved": []
            },
            "results": [],
            "recommendations": []
        }

        # Analyze results
        for result in self.results:
            report["results"].append({
                "test_name": result.test_name,
                "success_rate": (result.successful_requests / result.total_requests) * 100,
                "avg_latency_ms": result.avg_latency,
                "p95_latency_ms": result.p95_latency,
                "throughput_rps": result.throughput_rps,
                "error_rate_pct": result.error_rate * 100
            })

            # Track best metrics
            if result.p95_latency < report["summary"]["best_p95_latency"]:
                report["summary"]["best_p95_latency"] = result.p95_latency

            if result.throughput_rps > report["summary"]["best_throughput"]:
                report["summary"]["best_throughput"] = result.throughput_rps

        # Calculate overall success rate
        if self.results:
            total_successful = sum(r.successful_requests for r in self.results)
            total_requests = sum(r.total_requests for r in self.results)
            report["summary"]["overall_success_rate"] = (total_successful / total_requests) * 100

        # Check target achievements
        parallel_results = [r for r in self.results if "parallel" in r.test_name.lower()]
        sequential_results = [r for r in self.results if "sequential" in r.test_name.lower()]

        if parallel_results and sequential_results:
            avg_parallel_p95 = statistics.mean(r.p95_latency for r in parallel_results)
            avg_sequential_p95 = statistics.mean(r.p95_latency for r in sequential_results)
            improvement = ((avg_sequential_p95 - avg_parallel_p95) / avg_sequential_p95) * 100

            if improvement >= 60:
                report["summary"]["targets_achieved"].append("60%_latency_reduction")
            if avg_parallel_p95 <= 500:
                report["summary"]["targets_achieved"].append("p95_under_500ms")

        high_load_results = [r for r in self.results if "concurrent" in r.test_name]
        if high_load_results:
            max_throughput = max(r.throughput_rps for r in high_load_results)
            if max_throughput >= 500:
                report["summary"]["targets_achieved"].append("500_rps_throughput")

        # Generate recommendations
        if report["summary"]["best_p95_latency"] > 500:
            report["recommendations"].append("Optimize provider selection algorithm")

        if report["summary"]["best_throughput"] < 200:
            report["recommendations"].append("Improve concurrent request handling")

        if report["summary"]["overall_success_rate"] < 95:
            report["recommendations"].append("Enhance error handling and retry logic")

        return report

    def _save_benchmark_results(self, report: Dict[str, Any]):
        """Save benchmark results to file"""
        timestamp = int(time.time())
        filename = f"benchmark_results_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"💾 Benchmark results saved to {filename}")

    def _mock_providers_context(self):
        """Context manager for mocking provider factory and discovery"""
        from unittest.mock import patch
        import contextlib

        @contextlib.asynccontextmanager
        async def mock_context():
            def mock_get_provider(name):
                return self.test_providers.get(name)

            with patch('src.core.parallel_fallback.provider_factory') as mock_factory:
                mock_factory.get_provider = AsyncMock(side_effect=mock_get_provider)
                mock_factory.get_all_provider_info = AsyncMock(return_value=[
                    type('ProviderInfo', (), {
                        'name': name,
                        'status': 1,  # HEALTHY
                        'models': ['gpt-3.5-turbo']
                    })() for name in self.test_providers.keys()
                ])

                with patch.object(provider_discovery, 'get_healthy_providers_for_model',
                                return_value=list(self.test_providers.keys())):
                    yield

        return mock_context()


async def run_benchmarks():
    """Run the complete benchmark suite"""
    benchmark = ParallelExecutionBenchmark()
    report = await benchmark.run_full_benchmark_suite()

    print("\n" + "=" * 60)
    print("🏆 BENCHMARK SUITE COMPLETE")
    print("=" * 60)

    print(f"📊 Overall Success Rate: {report['summary']['overall_success_rate']:.1f}%")
    print(f"⚡ Best P95 Latency: {report['summary']['best_p95_latency']:.1f}ms")
    print(f"🚀 Best Throughput: {report['summary']['best_throughput']:.0f} req/s")

    targets = report['summary']['targets_achieved']
    if targets:
        print(f"✅ Targets Achieved: {', '.join(targets)}")
    else:
        print("❌ No targets achieved - optimization needed")

    if report['recommendations']:
        print("💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   • {rec}")

    return report


if __name__ == "__main__":
    # Run benchmarks when script is executed directly
    asyncio.run(run_benchmarks())