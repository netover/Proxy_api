"""
Optimized HTTP Client for Production Use
High-performance HTTP client with connection pooling, retries, and monitoring.
"""

import asyncio
import time
from typing import Dict, Any, Optional
import httpx
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class OptimizedHTTPClient:
    """
    Production-ready HTTP client with:
    - Connection pooling
    - Automatic retries with exponential backoff
    - Request/response monitoring
    - Circuit breaker integration
    - Memory-efficient streaming
    """

    def __init__(
        self,
        max_keepalive_connections: int = 100,
        max_connections: int = 1000,
        keepalive_expiry: float = 30.0,
        timeout: float = 30.0,
        connect_timeout: float = 10.0,
        retry_attempts: int = 3,
        retry_backoff_factor: float = 0.5,
        circuit_breaker=None,
    ):
        self.max_keepalive_connections = max_keepalive_connections
        self.max_connections = max_connections
        self.keepalive_expiry = keepalive_expiry
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.retry_attempts = retry_attempts
        self.retry_backoff_factor = retry_backoff_factor
        self.circuit_breaker = circuit_breaker

        # Metrics
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0

        # Initialize client
        self._client: Optional[httpx.AsyncClient] = None
        self._closed = False

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Initialize the HTTP client with optimized settings"""
        if self._client is not None:
            return

        limits = httpx.Limits(
            max_keepalive_connections=self.max_keepalive_connections,
            max_connections=self.max_connections,
            keepalive_expiry=self.keepalive_expiry,
        )

        timeout = httpx.Timeout(self.timeout, connect=self.connect_timeout)

        self._client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            follow_redirects=True,
            http2=True,  # Enable HTTP/2 for better performance
        )

        logger.info(
            "HTTP client initialized",
            extra={
                "max_keepalive": self.max_keepalive_connections,
                "max_connections": self.max_connections,
                "timeout": self.timeout,
            },
        )

    async def close(self):
        """Close the HTTP client and cleanup resources"""
        if self._client and not self._closed:
            await self._client.aclose()
            self._closed = True
            logger.info("HTTP client closed")

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ) -> httpx.Response:
        """
        Make HTTP request with automatic retries and monitoring
        """
        if self._client is None:
            await self.initialize()

        if self._closed:
            raise RuntimeError("HTTP client is closed")

        # Circuit breaker check
        if self.circuit_breaker:

            async def make_request():
                return await self._make_request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    data=data,
                    params=params,
                    stream=stream,
                    **kwargs,
                )

            return await self.circuit_breaker.execute(make_request)

        return await self._make_request(
            method,
            url,
            headers=headers,
            json=json,
            data=data,
            params=params,
            stream=stream,
            **kwargs,
        )

    async def _make_request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs,
    ) -> httpx.Response:
        """Internal request method with retry logic"""
        last_exception = None

        for attempt in range(self.retry_attempts + 1):
            try:
                start_time = time.time()

                # Make request
                response = await self._client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                    data=data,
                    params=params,
                    **kwargs,
                )

                response_time = time.time() - start_time

                # Update metrics
                self.request_count += 1
                self.total_response_time += response_time

                # Log successful request
                logger.info(
                    "HTTP request successful",
                    extra={
                        "method": method,
                        "url": url,
                        "status_code": response.status_code,
                        "response_time": round(response_time * 1000, 2),  # ms
                        "attempt": attempt + 1,
                    },
                )

                return response

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                self.error_count += 1

                if attempt < self.retry_attempts:
                    # Exponential backoff
                    delay = self.retry_backoff_factor * (2**attempt)
                    logger.warning(
                        "HTTP request failed, retrying",
                        extra={
                            "method": method,
                            "url": url,
                            "attempt": attempt + 1,
                            "max_attempts": self.retry_attempts + 1,
                            "delay": delay,
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "HTTP request failed after all retries",
                        extra={
                            "method": method,
                            "url": url,
                            "attempts": attempt + 1,
                            "error": str(e),
                        },
                    )

            except Exception as e:
                # Non-retryable errors
                self.error_count += 1
                logger.error(
                    "HTTP request failed with non-retryable error",
                    extra={
                        "method": method,
                        "url": url,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                raise

        # All retries exhausted
        raise last_exception

    def get_metrics(self) -> Dict[str, Any]:
        """Get client performance metrics"""
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0
            else 0
        )

        return {
            "requests_total": self.request_count,
            "errors_total": self.error_count,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "error_rate": (
                self.error_count / self.request_count if self.request_count > 0 else 0
            ),
            "max_connections": self.max_connections,
            "active_connections": (
                getattr(self._client, "_pool", {}).get("connections", 0)
                if self._client
                else 0
            ),
        }


# Backward compatibility alias
HTTPClient = OptimizedHTTPClient

# Global client instance for reuse
_http_client: Optional[OptimizedHTTPClient] = None


async def get_http_client() -> OptimizedHTTPClient:
    """Get or create global HTTP client instance"""
    global _http_client

    if _http_client is None or _http_client._closed:
        _http_client = OptimizedHTTPClient()

    if _http_client._client is None:
        await _http_client.initialize()

    return _http_client


@asynccontextmanager
async def http_client_context():
    """Context manager for HTTP client usage"""
    client = await get_http_client()
    try:
        yield client
    finally:
        # Don't close global client, let it be reused
        pass
