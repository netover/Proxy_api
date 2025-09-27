#!/usr/bin/env python3
"""
Test runner script for LLM Proxy API.

Usage: python scripts/run_tests.py [unit|integration|chaos|all]
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def main():
    """Main test runner function."""
    print("🧪 LLM Proxy API Test Suite")

    # Check Redis availability
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, db=0)
        client.ping()
        redis_available = True
        print("✅ Redis is available")
    except:
        redis_available = False
        print("⚠️  Redis not available - some tests will be skipped")

    # Determine test type
    test_type = sys.argv[1] if len(sys.argv) > 1 else "all"

    success = True

    if test_type in ["unit", "all"]:
        print("\n🏃 Running unit tests...")
        if not run_command("python -m pytest tests/test_unit/ -v", "Unit tests"):
            success = False

    if test_type in ["integration", "all"]:
        print("\n🔗 Running integration tests...")
        if not run_command("python -m pytest tests/test_integration/ -v", "Integration tests"):
            success = False

    if test_type in ["chaos", "all"]:
        print("\n🐒 Running chaos engineering tests...")
        if not run_command("python -m pytest tests/test_unit/test_chaos.py -v", "Chaos tests"):
            success = False

    if test_type == "all" and redis_available:
        print("\n🗄️  Running Redis tests...")
        if not run_command("python -m pytest -m redis -v", "Redis tests"):
            success = False

    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
