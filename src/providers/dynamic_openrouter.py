import time
from typing import Any, Dict

from src.core.metrics import metrics_collector
from src.providers.dynamic_base import DynamicProvider


class DynamicOpenRouterProvider(DynamicProvider):
    """Dynamic OpenRouter provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check OpenRouter API health"""
        try:
            response = await self.make_request(
                "GET",
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            models_data = response.json()
            return {
                "models_available": len(models_data.get("data", [])),
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with OpenRouter API"""
        start_time = time.time()
        try:
            # OpenRouter is OpenAI compatible, so we can pass the request mostly as-is.
            # It also supports extra headers for moderation and identification.
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://llm-proxy.agnos.ai",  # Example Referer
                    "X-Title": "LLM Proxy",  # Example Title
                },
            )
            result = response.json()
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=result.get("usage", {}).get("total_tokens", 0),
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
            self.logger.error(f"Chat completion failed: {e}")
            raise

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {**request, "messages": messages}
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by OpenRouter)"""
        raise NotImplementedError("OpenRouter provider does not support embeddings.")
