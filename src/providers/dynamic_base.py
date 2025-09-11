from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from src.providers.base import Provider
from src.core.app_config import ProviderConfig
from src.core.logging import ContextualLogger
import httpx
import asyncio

class DynamicProvider(Provider):
    """Base class for dynamically loaded AI providers"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    @abstractmethod
    async def _health_check(self) -> Dict[str, Any]:
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
        max_retries: int = 3,
        stream: bool = False,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic (exponential backoff + jitter) and error handling"""
        import random
        base_delay = 1.0
        
        for attempt in range(max_retries + 1):
            try:
                response = await self.client.request(method, url, stream=stream, **kwargs)
                if not stream:
                    response.raise_for_status()
                    return response
                else:
                    # For streaming, basic check but don't raise yet (handle in iterator)
                    if response.status_code >= 500:
                        response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as e:
                if attempt == max_retries:
                    if e.response.status_code == 404:
                        self.logger.error("Model not found (404)")
                        raise ValueError(f"Model not found: {e.response.text}")
                    elif e.response.status_code == 401:
                        self.logger.error("Authentication failed (401)")
                        raise ValueError(f"Authentication failed: {e.response.text}")
                    else:
                        self.logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                        raise
                # Retry with backoff + jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
            except httpx.RequestError as e:
                if attempt == max_retries:
                    self.logger.error(f"Request error: {e}")
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.warning(f"Request error (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
            except Exception as e:
                if attempt == max_retries:
                    self.logger.error(f"Unexpected error: {e}")
                    raise
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                self.logger.warning(f"Unexpected error (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s")
                await asyncio.sleep(delay)
