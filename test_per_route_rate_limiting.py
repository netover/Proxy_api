#!/usr/bin/env python3
"""
Test script for per-route rate limiting functionality.
This script tests that different endpoints have different rate limits applied.
"""

import asyncio
import time
import aiohttp
import json
from typing import Dict, List

class RateLimitTester:
    """Test per-route rate limiting functionality"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def make_request(self, endpoint: str, headers: Dict = None) -> Dict:
        """Make a single request to an endpoint"""
        url = f"{self.base_url}{endpoint}"
        default_headers = {"X-API-Key": "test-key-123"}
        if headers:
            default_headers.update(headers)

        try:
            async with self.session.get(url, headers=default_headers) as response:
                result = {
                    "status": response.status,
                    "endpoint": endpoint,
                    "rate_limit_hit": False
                }

                if response.status == 429:
                    result["rate_limit_hit"] = True
                    result["retry_after"] = response.headers.get("Retry-After")

                return result
        except Exception as e:
            return {
                "status": "error",
                "endpoint": endpoint,
                "error": str(e)
            }

    async def test_rate_limits(self, endpoints: List[str], requests_per_endpoint: int = 10) -> Dict:
        """Test rate limits for multiple endpoints"""
        results = {}

        for endpoint in endpoints:
            print(f"Testing {endpoint} with {requests_per_endpoint} requests...")
            endpoint_results = []

            # Make requests in quick succession to trigger rate limits
            for i in range(requests_per_endpoint):
                result = await self.make_request(endpoint)
                endpoint_results.append(result)

                if result.get("rate_limit_hit"):
                    print(f"  Rate limit hit on request {i+1}")
                    break

                # Small delay to avoid overwhelming
                await asyncio.sleep(0.1)

            results[endpoint] = endpoint_results

            # Wait a bit before testing next endpoint
            await asyncio.sleep(1)

        return results

    def analyze_results(self, results: Dict) -> Dict:
        """Analyze test results"""
        analysis = {}

        for endpoint, requests in results.items():
            rate_limit_hits = sum(1 for r in requests if r.get("rate_limit_hit"))
            total_requests = len(requests)
            first_hit_index = next((i for i, r in enumerate(requests) if r.get("rate_limit_hit")), None)

            analysis[endpoint] = {
                "total_requests": total_requests,
                "rate_limit_hits": rate_limit_hits,
                "first_rate_limit_at": first_hit_index,
                "rate_limit_percentage": (rate_limit_hits / total_requests) * 100 if total_requests > 0 else 0
            }

        return analysis

async def main():
    """Main test function"""
    endpoints_to_test = [
        "/health",           # Should allow 1000/minute
        "/v1/health",        # Should allow 1000/minute
        "/v1/models",        # Should allow 200/minute
        "/v1/status",        # Should allow 500/minute
        "/v1/metrics",       # Should allow 500/minute
        "/v1/providers",     # Should allow 200/minute
    ]

    print("Starting per-route rate limiting tests...")
    print("Expected limits:")
    print("  /health: 1000/minute")
    print("  /v1/health: 1000/minute")
    print("  /v1/models: 200/minute")
    print("  /v1/status: 500/minute")
    print("  /v1/metrics: 500/minute")
    print("  /v1/providers: 200/minute")
    print()

    async with RateLimitTester() as tester:
        # Test with fewer requests to avoid overwhelming the server
        results = await tester.test_rate_limits(endpoints_to_test, requests_per_endpoint=5)

        print("\nTest Results:")
        analysis = tester.analyze_results(results)

        for endpoint, stats in analysis.items():
            print(f"{endpoint}:")
            print(f"  Requests made: {stats['total_requests']}")
            print(f"  Rate limit hits: {stats['rate_limit_hits']}")
            print(".1f")
            if stats['first_rate_limit_at'] is not None:
                print(f"  First rate limit at request: {stats['first_rate_limit_at'] + 1}")
            print()

        print("Test completed!")

if __name__ == "__main__":
    asyncio.run(main())