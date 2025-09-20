import asyncio
import time
import httpx
import os
from collections import Counter

# --- Configuration ---
# The target URL for the stress test.
# Assumes the API is running on localhost:8000.
BASE_URL = os.getenv("STRESS_TEST_BASE_URL", "http://localhost:8000")
ENDPOINT = "/v1/chat/completions"
URL = f"{BASE_URL}{ENDPOINT}"

# Number of concurrent requests to send.
CONCURRENT_REQUESTS = 50

# Timeout for each request in seconds.
TIMEOUT = 30

# API key for authentication.
# Make sure this key is present in your config.yaml.
API_KEY = os.getenv("PROXY_API_KEY", "test-key-123")

# Request payload.
REQUEST_PAYLOAD = {
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Tell me a short joke."}],
}

# --- Stress Test Logic ---

async def send_request(client: httpx.AsyncClient, request_num: int):
    """Sends a single request and returns the status code."""
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
    try:
        start_time = time.monotonic()
        response = await client.post(URL, json=REQUEST_PAYLOAD, headers=headers, timeout=TIMEOUT)
        duration = time.monotonic() - start_time
        print(f"Request {request_num}: Status {response.status_code} in {duration:.2f}s")
        return response.status_code
    except httpx.ReadTimeout:
        print(f"Request {request_num}: Timed out after {TIMEOUT}s")
        return "timeout"
    except httpx.ConnectError as e:
        print(f"Request {request_num}: Connection error: {e}")
        return "connect_error"
    except Exception as e:
        print(f"Request {request_num}: An unexpected error occurred: {e}")
        return "exception"

async def main():
    """Runs the basic stress test."""
    print("--- Starting Basic Stress Test ---")
    print(f"Target: {URL}")
    print(f"Concurrent Requests: {CONCURRENT_REQUESTS}")
    print("------------------------------------")

    start_total_time = time.monotonic()

    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(CONCURRENT_REQUESTS)]
        results = await asyncio.gather(*tasks)

    total_duration = time.monotonic() - start_total_time

    print("--- Stress Test Finished ---")
    print(f"Total time: {total_duration:.2f}s")

    status_counts = Counter(results)

    print("\n--- Results Summary ---")
    for status, count in status_counts.items():
        print(f"Status '{status}': {count} requests")

    success_count = status_counts.get(200, 0)
    rate_limited_count = status_counts.get(429, 0)
    total_requests = len(results)

    print(f"\nSuccess Rate (200 OK): {success_count / total_requests:.2%}")
    if rate_limited_count > 0:
        print(f"Rate Limited (429): {rate_limited_count} requests")

    print("-------------------------")

if __name__ == "__main__":
    # This allows the script to be run directly.
    # Note: The API server must be running in a separate terminal.
    asyncio.run(main())
