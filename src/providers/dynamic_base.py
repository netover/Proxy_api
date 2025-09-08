from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import asyncio
import httpx
import time
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from src.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenException
import os


class DynamicProvider(ABC):
    """Base class for dynamically loaded AI providers"""

    def __init__(self, name: str, api_key: str, base_url: str, models: List[str], priority: int):
        self.name = name
        self.api_key = api_key or ""
        self.base_url = base_url
        self.models = models
        self.priority = priority
        self.logger = ContextualLogger(f"provider.{name}")

        # Connection pooling setup
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            ),
            headers={
                "User-Agent": "LLM-Proxy-API/1.0"
            }
        )

        if not self.api_key:
            self.logger.warning(f"API key for {name} not found in environment")


    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        start_time = time.time()
        try:
            result = await self._health_check()
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                error_type=None
            )

            return {
                "status": "healthy" if result else "unhealthy",
                "response_time": response_time,
                "details": result
            }
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": f"Unexpected error: {str(e)}"
            }

    @abstractmethod
    async def _health_check(self) -> Any:
        """Internal health check implementation"""
        pass

    @abstractmethod
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using the provider's API"""
        pass

    @abstractmethod
    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using the provider's API"""
        pass

    @abstractmethod
    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using the provider's API"""
        pass

    async def make_request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic and circuit breaker"""
        # Get circuit breaker for this provider
        circuit_breaker = get_circuit_breaker(
            f"provider_{self.name}",
            failure_threshold=4,
            recovery_timeout=60  # 1 minute
        )
        
        async def _make_request() -> httpx.Response:
            """Internal request function"""
            last_exception = None

            # Include the initial attempt in the loop
            for attempt in range(3 + 1):  # 3 retry attempts
                try:
                    if attempt > 0:
                        await asyncio.sleep(1.0 * (2 ** (attempt - 1)))

                    response = await self.client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response

                except httpx.HTTPStatusError as e:
                    last_exception = e
                    # Check if we should retry (attempt < 3)
                    if attempt < 3:
                        self.logger.warning(
                            f"Request attempt {attempt + 1} failed with HTTP {e.response.status_code}: {e.response.text}, retrying..."
                        )
                    continue
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    last_exception = e
                    # Check if we should retry (attempt < 3)
                    if attempt < 3:
                        self.logger.warning(
                            f"Request attempt {attempt + 1} failed with connection error: {e}, retrying..."
                        )
                    continue
                except Exception as e:
                    last_exception = e
                    self.logger.error(f"Unexpected error during request: {e}")
                    break

            raise last_exception
        
        # Execute with circuit breaker
        try:
            return await circuit_breaker.execute(_make_request)
        except CircuitBreakerOpenException:
            self.logger.error(f"Circuit breaker is open for provider {self.name}")
            raise httpx.RequestError(f"Circuit breaker is open for provider {self.name}", request=None)
        except Exception as e:
            self.logger.error(f"Request failed after all retries: {e}")
            raise

            
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
