from typing import Dict, Any
import httpx
from src.providers.dynamic_base import DynamicProvider
from src.core.metrics import metrics_collector
import time

class DynamicPerplexityProvider(DynamicProvider):
    """Dynamic Perplexity provider implementation"""

    async def _health_check(self) -> Dict[str, Any]:
        """Check Perplexity health"""
        # Perplexity doesn't have a standard health check endpoint
        # We'll just return a basic status
        return {"status": "ok"}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using Perplexity's API"""
        start_time = time.time()

        try:
            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/chat/completions",
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
                self.name,
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
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Chat completion failed: {e}")
            raise

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using Perplexity's API"""
        # Perplexity primarily focuses on chat completions
        # We'll implement the same as create_completion
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Perplexity's API"""
        # Perplexity doesn't have a native embeddings API
        # We'll raise an exception indicating this feature is not supported
        raise NotImplementedError("Perplexity provider does not support embeddings")
