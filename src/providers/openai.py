from typing import Dict, Any
import httpx
from src.providers.base import Provider
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import time

class OpenAIProvider(Provider):
    """OpenAI provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _health_check(self) -> Dict[str, Any]:
        """Check OpenAI health"""
        try:
            response = await self.make_request_with_retry(
                "GET",
                f"{self.config.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using OpenAI's API"""
        start_time = time.time()

        try:
            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request
            )

            result = response.json()

            # Record metrics
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)

            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Chat completion successful",
                           response_time=response_time,
                           tokens=tokens)

            return result

        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Chat completion failed: {e}")
            raise

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using OpenAI's API"""
        start_time = time.time()

        try:
            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.config.base_url}/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request
            )

            result = response.json()

            # Record metrics
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)

            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Text completion successful",
                           response_time=response_time,
                           tokens=tokens)

            return result

        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Text completion failed: {e}")
            raise

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI's API"""
        start_time = time.time()

        try:
            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.config.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request
            )

            result = response.json()

            # Record metrics
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)

            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Embeddings creation successful",
                           response_time=response_time,
                           tokens=tokens)

            return result

        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Embeddings creation failed: {e}")
            raise
