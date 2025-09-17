import time
from typing import Any, Dict

from src.core.metrics import metrics_collector
from src.providers.dynamic_base import DynamicProvider


class DynamicPerplexityProvider(DynamicProvider):
    """Dynamic Perplexity provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Perplexity health by listing models."""
        try:
            response = await self.make_request(
                "GET",
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def _make_request(
        self, request: Dict[str, Any], request_type: str
    ) -> Dict[str, Any]:
        """Helper to make requests to Perplexity's API and handle metrics."""
        start_time = time.time()
        try:
            response = await self.make_request(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=request,
            )
            result = response.json()
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=tokens,
            )
            self.logger.info(
                f"{request_type} successful",
                response_time=response_time,
                tokens=tokens,
            )
            return result
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__,
            )
            self.logger.error(f"{request_type} failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using Perplexity's API."""
        return await self._make_request(request, "Chat completion")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using Perplexity's API by adapting the request."""
        # Adapt the text completion request to a chat completion format
        chat_request = {
            "model": request.get("model"),
            "messages": [{"role": "user", "content": request.get("prompt", "")}],
            "max_tokens": request.get("max_tokens", 1024),
            "temperature": request.get("temperature", 0.7),
        }
        # Perplexity API is OpenAI-compatible, so the response is also compatible
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Perplexity's API (not supported)."""
        raise NotImplementedError("Perplexity provider does not support embeddings")
