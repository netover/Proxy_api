from abc import abstractmethod
from typing import Any, Dict

from src.core.logging import ContextualLogger
from src.core.providers.factory import BaseProvider
from src.core.config.models import ProviderConfig


class DynamicProvider(BaseProvider):
    """Base class for dynamically loaded AI providers"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    @abstractmethod
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Internal health check implementation"""

    @abstractmethod
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using the provider's API"""

    @abstractmethod
    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using the provider's API"""

    @abstractmethod
    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using the provider's API"""

    # Note: make_request_with_retry removed - use the base Provider's make_request method instead
