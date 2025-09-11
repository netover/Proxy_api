from typing import Dict, Any
import httpx
from src.providers.dynamic_base import DynamicProvider
from src.core.metrics import metrics_collector
import time

class DynamicAnthropicProvider(DynamicProvider):
    """Dynamic Anthropic provider implementation"""

    async def _health_check(self) -> Dict[str, Any]:
        """Check Anthropic health"""
        try:
            response = await self.make_request(
                "GET",
                f"{self.base_url}/v1/models",  # Adjusted for Anthropic API
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    def _map_finish_reason(self, reason: str) -> str:
        """Maps Anthropic's stop reason to OpenAI's finish reason."""
        return {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop",
        }.get(reason, "stop")

    async def _make_request(self, anthropic_request: Dict[str, Any], request_type: str) -> Dict[str, Any]:
        """Helper to make requests to the Anthropic API and handle metrics."""
        start_time = time.time()
        try:
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=anthropic_request
            )
            result = response.json()
            response_time = time.time() - start_time
            tokens = result.get("usage", {}).get("input_tokens", 0) + result.get("usage", {}).get("output_tokens", 0)
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
                        "content": result.get("content", [{}])[0].get("text", "")
                    },
                    "finish_reason": self._map_finish_reason(result.get("stop_reason"))
                }
            ],
            "usage": result.get("usage")
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
                    "finish_reason": self._map_finish_reason(result.get("stop_reason"))
                }
            ],
            "usage": result.get("usage")
        }

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Anthropic's API"""
        # Anthropic doesn't have a native embeddings API
        # We'll raise an exception indicating this feature is not supported
        raise NotImplementedError("Anthropic provider does not support embeddings")
