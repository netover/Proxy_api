from typing import Dict, Any
import httpx
from src.providers.dynamic_base import DynamicProvider
from src.core.metrics import metrics_collector
import time

class DynamicOpenAIProvider(DynamicProvider):
    """Dynamic OpenAI provider implementation"""

    async def _health_check(self) -> Dict[str, Any]:
        """Check OpenAI health"""
        try:
            response = await self.make_request_with_retry(
                "GET",
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def _make_request(self, endpoint: str, request: Dict[str, Any], request_type: str) -> Dict[str, Any]:
        """Helper to make requests to OpenAI-like APIs and handle metrics"""
        start_time = time.time()
        try:
            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=request
            )
            result = response.json()
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("total_tokens", 0)
            metrics_collector.record_request(
                self.name, success=True, response_time=response_time, tokens=tokens
            )
            self.logger.info(f"{request_type} successful", response_time=response_time, tokens=tokens)
            return result
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name, success=False, response_time=response_time, error_type=type(e).__name__
            )
            self.logger.error(f"{request_type} failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using OpenAI's API"""
        return await self._make_request("chat/completions", request, "Chat completion")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using OpenAI's API"""
        return await self._make_request("completions", request, "Text completion")

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI's API"""
        return await self._make_request("embeddings", request, "Embeddings creation")
