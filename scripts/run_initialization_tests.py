#!/usr/bin/env python3
"""
Script to run initialization stability tests and generate detailed report.
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_initialization_scenarios import run_initialization_tests

async def main():
    """Run initialization tests and print detailed report."""
    print("="*80)
    print("PROXYAPI INITIALIZATION STABILITY TEST SUITE")
    print("="*80)
    print()

    try:
        report = await run_initialization_tests()

        print("\n" + "="*60)
        print("DETAILED TEST REPORT")
        print("="*60)

        summary = report["test_summary"]
        print(f"Total Scenarios Tested: {summary['total_scenarios']}")
        print(f"[PASS] Passed: {summary['passed']}")
        print(f"[FAIL] Failed: {summary['failed']}")
        print(f"[WARN] Warnings: {summary['warnings']}")
        print()

        if report["failure_modes"]:
            print("FAILURE MODES IDENTIFIED:")
            print("-" * 40)
            for failure in report["failure_modes"]:
                status_icon = "[FAIL]" if failure["status"] == "failed" else "[WARN]"
                print(f"{status_icon} {failure['scenario']}: {failure['error']}")
            print()

        print("RECOMMENDATIONS:")
        print("-" * 40)
        for rec in report["recommendations"]:
            priority_icon = {
                "high": "[HIGH]",
                "medium": "[MED]",
                "low": "[LOW]"
            }.get(rec["priority"], "[UNK]")

            print(f"{priority_icon} [{rec['priority'].upper()}] {rec['description']}")
            if rec.get('rationale'):
                print(f"   Reason: {rec['rationale']}")
            if 'details' in rec:
                print("   Details:")
                for detail in rec['details']:
                    print(f"   - {detail}")
            print()

        print("="*80)
        print("TEST EXECUTION COMPLETE")
        print("="*80)

        # Return appropriate exit code
        if summary['failed'] > 0:
            print(f"\n[CRITICAL] {summary['failed']} critical failures detected")
            return 1
        elif summary['warnings'] > 0:
            print(f"\n[WARNING] {summary['warnings']} warnings detected")
            return 0
        else:
            print(f"\n[SUCCESS] All {summary['total_scenarios']} scenarios passed successfully")
            return 0

    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)