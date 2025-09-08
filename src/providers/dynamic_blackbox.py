from typing import Dict, Any
from src.providers.dynamic_base import DynamicProvider
from src.core.metrics import metrics_collector
import time

class DynamicBlackboxProvider(DynamicProvider):
    """Dynamic Blackbox.ai provider implementation"""

    async def _health_check(self) -> Dict[str, Any]:
        """Check Blackbox API health"""
        try:
            response = await self.make_request_with_retry(
                "GET",
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return {"models_available": len(response.json().get("data", []))}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with Blackbox API"""
        start_time = time.time()
        try:
            # Blackbox is mostly OpenAI compatible.
            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            result = response.json()
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=result.get("usage", {}).get("total_tokens", 0)
            )
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
        """Create text completion (mapped to chat completion)"""
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {**request, "messages": messages}
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Blackbox)"""
        raise NotImplementedError("Blackbox.ai does not support embeddings.")
