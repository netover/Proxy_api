from abc import ABC, abstractmethod
from typing import Dict, Any, Union
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
from src.core.logging import ContextualLogger
import httpx
import asyncio

class DynamicProvider(BaseProvider):
    """Base class for dynamically loaded AI providers"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    @abstractmethod
    async def _perform_health_check(self) -> Dict[str, Any]:
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

    # Note: make_request_with_retry removed - use the base Provider's make_request method instead
