from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import httpx
import time
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import os

class Provider(ABC):
    """Abstract base class for AI providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env, "")
        self.logger = ContextualLogger(f"provider.{config.name}")

        # Connection pooling setup
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(config.timeout),
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            ),
            headers={
                "User-Agent": "LLM-Proxy-API/1.0",
                **(config.headers or {})
            }
        )

        if not self.api_key:
            self.logger.warning(f"API key for {config.name} not found in environment")

    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        start_time = time.time()
        try:
            result = await self._health_check()
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                error_type=None
            )

            return {
                "status": "healthy" if result else "unhealthy",
                "response_time": response_time,
                "details": result
            }
        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": str(e)
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
        """Make HTTP request with retry logic"""
        last_exception = None

        # Include the initial attempt in the loop
        for attempt in range(self.config.retry_attempts + 1):
            try:
                if attempt > 0:
                    await asyncio.sleep(self.config.retry_delay * (2 ** (attempt - 1)))

                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()
                return response

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e
                # Check if we should retry (attempt < retry_attempts)
                if attempt < self.config.retry_attempts:
                    self.logger.warning(
                        f"Request attempt {attempt + 1} failed: {e}, retrying..."
                    )
                continue
            except Exception as e:
                last_exception = e
                break

        raise last_exception
            
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# Import implementations after base class
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider

# Provider factory
PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider
}

def get_provider(config: ProviderConfig) -> Provider:
    """Factory function to get provider instance"""
    provider_class = PROVIDER_CLASSES.get(config.type.lower())
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {config.type}")
    return provider_class(config)
