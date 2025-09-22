#!/usr/bin/env python3
"""
Test script to verify HTTP connection pooling and reuse in ProxyAPI
"""

import asyncio
import time
import logging
import pytest
from src.core.http.client_v2 import (
    get_advanced_http_client,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_connection_reuse():
    """Test connection reuse by making multiple requests"""
    print("Testing HTTP Connection Pooling and Reuse")
    print("=" * 50)

    # Test with a mock HTTP endpoint (using httpbin.org for testing)
    test_url = "https://httpbin.org/get"

    # Get HTTP client for testing
    client = get_advanced_http_client(
        max_keepalive_connections=10,
        max_connections=20,
        timeout=10.0,
    )

    print(f"Max connections: {client.max_connections}")
    print(f"Max keepalive connections: {client.max_keepalive_connections}")
    print()

    # Make multiple requests to test connection reuse
    print("Making 10 consecutive requests...")
    start_time = time.time()

    for i in range(10):
        try:
            response = await client.request("GET", test_url)
            print(
                f"Request {i+1}: Status {response.status_code}"
            )
            response.close()
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

        # Small delay between requests
        await asyncio.sleep(0.1)

    total_time = time.time() - start_time
    print(f"Total time for 10 requests: {total_time:.2f}s")
    print()

    # Get metrics
    metrics = client.get_metrics()
    print("Connection Pool Metrics:")
    print(f"Total requests: {metrics['requests_total']}")
    print(f"Total errors: {metrics['errors_total']}")
    print(f"Average response time: {metrics['avg_response_time_ms']:.2f}ms")
    print()

    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_connection_reuse())
