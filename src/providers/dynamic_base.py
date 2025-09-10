from abc import ABC, abstractmethod
from typing import Dict, Any
from src.providers.base import Provider
from src.core.app_config import ProviderConfig
from src.core.logging import ContextualLogger
import httpx

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
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic and error handling"""
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                self.logger.error("Model not found (404)")
                raise ValueError(f"Model not found: {e.response.text}")
            elif e.response.status_code == 401:
                self.logger.error("Authentication failed (401)")
                raise ValueError(f"Authentication failed: {e.response.text}")
            else:
                self.logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
        except httpx.RequestError as e:
            self.logger.error(f"Request error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise
