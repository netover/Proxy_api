#!/usr/bin/env python3
"""
Test Runner for Parallel Execution System
Executes all parallel execution tests and generates a summary report
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark_parallel_execution import run_benchmarks


async def run_test_suite():
    """Run the complete test suite"""
    print("🧪 PARALLEL EXECUTION TEST SUITE")
    print("=" * 50)

    start_time = time.time()

    try:
        # Run comprehensive benchmarks
        print("📊 Running Performance Benchmarks...")
        benchmark_report = await run_benchmarks()

        total_time = time.time() - start_time

        print(f"\n⏱️  Total Test Time: {total_time:.2f}s")
        print("\n" + "=" * 50)
        print("🏆 TEST SUITE SUMMARY")
        print("=" * 50)

        # Check if targets were achieved
        targets = benchmark_report.get("summary", {}).get("targets_achieved", [])
        if targets:
            print(f"✅ TARGETS ACHIEVED: {len(targets)}")
            for target in targets:
                print(f"   • {target.replace('_', ' ').title()}")
        else:
            print("❌ NO TARGETS ACHIEVED")
            print("   Optimization needed before production deployment")

        # Performance summary
        summary = benchmark_report.get("summary", {})
        print("\n📈 PERFORMANCE SUMMARY:")
        print(f"Overall Success Rate: {summary.get('overall_success_rate', 0):.1f}%")
        print(f"Best P95 Latency: {summary.get('best_p95_latency', 0):.1f}ms")
        print(f"Best Throughput: {summary.get('best_throughput', 0):.1f} req/s")

        # Recommendations
        recommendations = benchmark_report.get("recommendations", [])
        if recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                print(f"   • {rec}")

        return benchmark_report

    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def run_unit_tests():
    """Run unit tests using pytest if available"""
    try:
        import subprocess

        print("\n🧪 Running Unit Tests...")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_parallel_execution.py",
                "tests/test_chaos_parallel_execution.py",
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0

    except ImportError:
        print("⚠️  Pytest not available, skipping unit tests")
        return True
    except Exception as e:
        print(f"⚠️  Unit test execution failed: {e}")
        return False


async def main():
    """Main test runner"""
    print("🚀 Starting Parallel Execution System Test Suite\n")

    # Run unit tests first
    unit_tests_passed = run_unit_tests()

    # Run integration benchmarks
    benchmark_report = await run_test_suite()

    # Final status
    print("\n" + "=" * 50)
    if unit_tests_passed and benchmark_report:
        targets_achieved = benchmark_report.get("summary", {}).get(
            "targets_achieved", []
        )
        if targets_achieved:
            print("🎉 ALL TESTS PASSED - READY FOR PRODUCTION!")
            sys.exit(0)
        else:
            print("⚠️  TESTS PASSED BUT TARGETS NOT ACHIEVED")
            print("   Review recommendations before production deployment")
            sys.exit(1)
    else:
        print("❌ TEST SUITE FAILED")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
