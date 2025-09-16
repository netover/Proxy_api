#!/usr/bin/env python3
"""
Test script to demonstrate rate limiting with excessive requests.
This script sends multiple requests to the rate-limited endpoints
to show how the system responds to excessive traffic.
"""

import asyncio
import time
import aiohttp
import json
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict


class RateLimitTester:
    """Test class for demonstrating rate limiting functionality"""

    def __init__(
        self,
        base_url="http://localhost:8000",
        num_threads=10,
        requests_per_thread=20,
    ):
        self.base_url = base_url
        self.num_threads = num_threads
        self.requests_per_thread = requests_per_thread
        self.stats = defaultdict(int)
        self.lock = threading.Lock()
        self.client_session = None

    async def make_request(self, endpoint, client):
        """Make a single request and record the result"""
        url = f"{self.base_url}{endpoint}"
        try:
            start_time = time.time()
            async with client.get(url) as response:
                end_time = time.time()
                response_time = end_time - start_time

                with self.lock:
                    if response.status == 200:
                        self.stats["success"] += 1
                        print(
                            f"✅ {endpoint} - {response.status} ({response_time:.2f}s)"
                        )
                    elif response.status == 429:
                        self.stats["rate_limited"] += 1
                        retry_after = response.headers.get(
                            "Retry-After", "unknown"
                        )
                        print(
                            f"🚫 {endpoint} - {response.status} (Rate limited, retry after: {retry_after}s) ({response_time:.2f}s)"
                        )
                    else:
                        self.stats["error"] += 1
                        print(
                            f"❌ {endpoint} - {response.status} ({response_time:.2f}s)"
                        )

        except Exception as e:
            with self.lock:
                self.stats["exception"] += 1
                print(f"💥 {endpoint} - Exception: {e}")

    async def test_endpoint(self, endpoint, client):
        """Test a specific endpoint with multiple requests"""
        print(
            f"\n📡 Testing {endpoint} with {self.requests_per_thread} requests..."
        )
        tasks = []

        for _ in range(self.requests_per_thread):
            tasks.append(self.make_request(endpoint, client))

        await asyncio.gather(*tasks, return_exceptions=True)

    async def run_tests(self):
        """Run all rate limiting tests"""
        print("🚀 Starting Rate Limit Testing")
        print(f"Target: {self.base_url}")
        print(f"Threads: {self.num_threads}")
        print(f"Requests per thread: {self.requests_per_thread}")

        async with aiohttp.ClientSession() as client:
            # Test each rate-limited endpoint
            endpoints = ["/v1/models", "/v1/providers", "/v1/cache/stats"]

            for endpoint in endpoints:
                await self.test_endpoint(endpoint, client)

        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 RATE LIMITING TEST SUMMARY")
        print("=" * 60)
        print(f"Total Success Responses: {self.stats['success']}")
        print(f"Rate Limited Responses: {self.stats['rate_limited']}")
        print(f"Error Responses: {self.stats['error']}")
        print(f"Exceptions: {self.stats['exception']}")
        print()

        total_requests = sum(self.stats.values())
        if total_requests > 0:
            rate_limited_percentage = (
                self.stats["rate_limited"] / total_requests
            ) * 100
            print(".1f")
            print(
                f"Success Rate: {(self.stats['success'] / total_requests) * 100:.1f}%"
            )
        print("=" * 60)


async def main():
    """Main function to run rate limiting tests"""
    print("🔥 Rate Limiting Stress Test")
    print("This will send many requests to test rate limiting")
    print("Make sure your FastAPI server is running on localhost:8000")
    print()

    # Initialize tester with moderate load
    tester = RateLimitTester(
        base_url="http://localhost:8000",
        num_threads=5,  # 5 threads
        requests_per_thread=15,  # 15 requests each = 75 total per endpoint
    )

    try:
        await tester.run_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        tester.print_summary()
    except Exception as e:
        print(f"\n💥 Test failed: {e}")
        tester.print_summary()


if __name__ == "__main__":
    print("Rate Limit Tester")
    print("=================")
    print()
    print("Instructions:")
    print("1. Start your FastAPI server: python main.py")
    print("2. Run this script: python test_excessive_requests.py")
    print("3. Watch the rate limiting in action!")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
