#!/usr/bin/env python3
"""
Test script to verify HTTP connection pooling and reuse in ProxyAPI
"""

import asyncio
import time
import logging
from src.core.http_client_v2 import (
    get_advanced_http_client,
    get_all_client_metrics,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_connection_reuse():
    """Test connection reuse by making multiple requests"""
    print("Testing HTTP Connection Pooling and Reuse")
    print("=" * 50)

    # Test with a mock HTTP endpoint (using httpbin.org for testing)
    test_url = "https://httpbin.org/get"

    # Get HTTP client for testing
    client = get_advanced_http_client(
        provider_name="test_provider",
        max_keepalive_connections=10,
        max_connections=20,
        timeout=10.0,
    )

    print(f"Testing with client: {client.provider_name}")
    print(f"Max connections: {client.max_connections}")
    print(f"Max keepalive connections: {client.max_keepalive_connections}")
    print()

    # Make multiple requests to test connection reuse
    print("Making 10 consecutive requests...")
    start_time = time.time()

    for i in range(10):
        try:
            response = await client.request("GET", test_url)
            async with response:
                print(
                    f"Request {i+1}: Status {response.status_code}, "
                    f"Connection reused: {client.connection_reuse_count > 0}"
                )
                # Response is automatically closed by async context manager
        except Exception as e:
            print(f"Request {i+1} failed: {e}")

        # Small delay between requests
        await asyncio.sleep(0.1)

    total_time = time.time() - start_time
    print(".2f")
    print()

    # Get metrics
    metrics = client.get_metrics()
    print("Connection Pool Metrics:")
    print(f"Total requests: {metrics['requests_total']}")
    print(f"Connection reuse count: {metrics['connection_reuse_count']}")
    print(f"New connection count: {metrics['new_connection_count']}")
    print(".1%")
    print(f"Average response time: {metrics['avg_response_time_ms']:.2f}ms")
    print()

    # Show pool information
    pool_info = metrics.get("pool_info", {})
    if pool_info:
        print("Connection Pool Status:")
        print(f"Total connections: {pool_info.get('total_connections', 0)}")
        print(
            f"Available connections: {pool_info.get('available_connections', 0)}"
        )
        print(
            f"Pending connections: {pool_info.get('pending_connections', 0)}"
        )
    print()

    # Test client registry
    print("Testing HTTP Client Registry...")
    all_metrics = get_all_client_metrics()
    print(f"Total registered clients: {len(all_metrics)}")
    for provider_name, provider_metrics in all_metrics.items():
        print(
            f"  {provider_name}: {provider_metrics.get('requests_total', 0)} requests"
        )

    print("\nTest completed successfully!")
    print(
        "Connection reuse verification: PASSED"
        if metrics["connection_reuse_rate"] > 0
        else "FAILED"
    )


if __name__ == "__main__":
    asyncio.run(test_connection_reuse())
