import time
from typing import Any, Dict

from src.core.metrics import metrics_collector
from src.providers.dynamic_base import DynamicProvider


class DynamicAzureOpenAIProvider(DynamicProvider):
    """Dynamic Azure OpenAI provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Azure OpenAI health with comprehensive validation"""
        start_time = time.time()
        try:
            # Azure OpenAI uses a different endpoint structure
            # We'll test with a simple chat completion
            test_request = {
                "model": self.models[0] if self.models else "gpt-35-turbo",  # Use first available model
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }

            response = await self.make_request(
                "POST",
                f"{self.base_url}/openai/deployments/{test_request['model']}/chat/completions",
                headers={
                    "api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=test_request,
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
            if not isinstance(data, dict):
                return {
                    "healthy": False,
                    "error": "Invalid response structure from API",
                    "response_time": time.time() - start_time
                }

            # Check for required fields
            if "choices" not in data or not isinstance(data["choices"], list):
                return {
                    "healthy": False,
                    "error": "Missing or invalid choices in response",
                    "response_time": time.time() - start_time
                }

            if len(data["choices"]) == 0:
                return {
                    "healthy": False,
                    "error": "Empty choices in response",
                    "response_time": time.time() - start_time
                }

            # Check usage information
            usage = data.get("usage", {})
            if not isinstance(usage, dict):
                return {
                    "healthy": False,
                    "error": "Invalid usage information",
                    "response_time": time.time() - start_time
                }

            return {
                "healthy": True,
                "model_used": data.get("model", "unknown"),
                "tokens_used": usage.get("total_tokens", 0),
                "response_time": time.time() - start_time,
                "details": {
                    "deployment": test_request["model"],
                    "api_version": "2023-05-15",  # Azure OpenAI API version
                    "provider": "azure_openai"
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
        """Helper to make requests to Azure OpenAI API and handle metrics"""
        start_time = time.time()
        try:
            # Azure OpenAI requires the model to be in the deployment path
            model = request.get("model", self.models[0] if self.models else "gpt-35-turbo")

            response = await self.make_request(
                "POST",
                f"{self.base_url}/openai/deployments/{model}/{endpoint}",
                headers={
                    "api-key": self.api_key,
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
        """Create a chat completion using Azure OpenAI's API"""
        return await self._make_request("chat/completions", request, "Chat completion")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using Azure OpenAI's API"""
        # Map text completion to chat completion format
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {**request, "messages": messages}
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Azure OpenAI's API"""
        return await self._make_request("embeddings", request, "Embeddings creation")
