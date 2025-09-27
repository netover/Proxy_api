import time
from typing import Any, Dict

from src.core.metrics import metrics_collector
from src.providers.dynamic_base import DynamicProvider


class DynamicAnthropicProvider(DynamicProvider):
    """Dynamic Anthropic provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Anthropic health with comprehensive validation"""
        start_time = time.time()
        try:
            # Test basic connectivity with a simple message
            test_request = {
                "model": "claude-3-haiku-20240307",  # Use a lightweight model
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            }

            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
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
            if "content" not in data:
                return {
                    "healthy": False,
                    "error": "Missing content in response",
                    "response_time": time.time() - start_time
                }

            content = data.get("content", [])
            if not isinstance(content, list) or len(content) == 0:
                return {
                    "healthy": False,
                    "error": "Empty or invalid content in response",
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
                "tokens_used": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
                "response_time": time.time() - start_time,
                "details": {
                    "api_version": "2023-06-01",
                    "model_family": data.get("model", "").split("-")[0] if data.get("model") else "unknown"
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

    def _map_finish_reason(self, reason: str) -> str:
        """Maps Anthropic's stop reason to OpenAI's finish reason."""
        return {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
        }.get(reason, "stop")

    async def _make_request(
        self, anthropic_request: Dict[str, Any], request_type: str
    ) -> Dict[str, Any]:
        """Helper to make requests to the Anthropic API and handle metrics."""
        start_time = time.time()
        try:
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=anthropic_request,
            )
            result = response.json()
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("input_tokens", 0) + result.get(
                "usage", {}
            ).get("output_tokens", 0)
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
        """Create a chat completion using Anthropic's API"""
        anthropic_request = {
            "model": request.get("model"),
            "messages": request.get("messages", []),
            "max_tokens": request.get("max_tokens", 1024),
            "temperature": request.get("temperature", 0.7),
            "stream": request.get("stream", False),
        }
        result = await self._make_request(anthropic_request, "Chat completion")

        return {
            "id": result.get("id"),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": result.get("model"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": result.get("content", [{}])[0].get("text", ""),
                    },
                    "finish_reason": self._map_finish_reason(result.get("stop_reason")),
                }
            ],
            "usage": result.get("usage"),
        }

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using Anthropic's API by adapting the prompt."""
        prompt = request.get("prompt", "")
        anthropic_request = {
            "model": request.get("model"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": request.get("max_tokens", 1024),
            "temperature": request.get("temperature", 0.7),
            "stream": request.get("stream", False),
        }
        result = await self._make_request(anthropic_request, "Text completion")

        return {
            "id": result.get("id"),
            "object": "text_completion",
            "created": int(time.time()),
            "model": result.get("model"),
            "choices": [
                {
                    "text": result.get("content", [{}])[0].get("text", ""),
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": self._map_finish_reason(result.get("stop_reason")),
                }
            ],
            "usage": result.get("usage"),
        }

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Anthropic's API"""
        # Anthropic doesn't have a native embeddings API
        # We'll raise an exception indicating this feature is not supported
        raise NotImplementedError("Anthropic provider does not support embeddings")
