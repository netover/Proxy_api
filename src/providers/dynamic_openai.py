import time
from typing import Any, Dict

from src.core.metrics import metrics_collector
from src.providers.dynamic_base import DynamicProvider


class DynamicOpenAIProvider(DynamicProvider):
    """Dynamic OpenAI provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check OpenAI health with comprehensive validation"""
        start_time = time.time()
        try:
            # Test basic connectivity
            response = await self.make_request(
                "GET",
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0  # Faster timeout for health checks
            )

            if response.status_code != 200:
                return {
                    "healthy": False,
                    "error": f"API returned status {response.status_code}",
                    "response_time": time.time() - start_time
                }

            data = response.json()

            # Validate response structure
            if not isinstance(data, dict) or "data" not in data:
                return {
                    "healthy": False,
                    "error": "Invalid response structure from API",
                    "response_time": time.time() - start_time
                }

            models = data.get("data", [])
            if not isinstance(models, list):
                return {
                    "healthy": False,
                    "error": "Models data is not a list",
                    "response_time": time.time() - start_time
                }

            # Check if we have at least one model
            if len(models) == 0:
                return {
                    "healthy": False,
                    "error": "No models available",
                    "response_time": time.time() - start_time
                }

            # Check API key validity by examining first model
            first_model = models[0]
            if not isinstance(first_model, dict) or "id" not in first_model:
                return {
                    "healthy": False,
                    "error": "Invalid model structure",
                    "response_time": time.time() - start_time
                }

            return {
                "healthy": True,
                "models_count": len(models),
                "first_model": first_model.get("id"),
                "api_version": data.get("object", "unknown"),
                "response_time": time.time() - start_time,
                "details": {
                    "total_models": len(models),
                    "models_sample": [m.get("id") for m in models[:5]]  # First 5 models
                }
            }

        except Exception as e:
            response_time = time.time() - start_time
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "response_time": response_time
            }

    async def _make_request(
        self, endpoint: str, request: Dict[str, Any], request_type: str
    ) -> Dict[str, Any]:
        """Helper to make requests to OpenAI-like APIs and handle metrics"""
        start_time = time.time()
        try:
            response = await self.make_request(
                "POST",
                f"{self.base_url}/{endpoint}",
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
        """Create a chat completion using OpenAI's API"""
        return await self._make_request("chat/completions", request, "Chat completion")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using OpenAI's API"""
        return await self._make_request("completions", request, "Text completion")

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI's API"""
        return await self._make_request("embeddings", request, "Embeddings creation")
