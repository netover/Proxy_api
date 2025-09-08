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
            response = await self.make_request_with_retry(
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

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using Anthropic's API"""
        start_time = time.time()

        try:
            # Convert OpenAI-style request to Anthropic format
            anthropic_request = {
                "model": request.get("model"),
                "messages": request.get("messages", []),
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "stream": request.get("stream", False)
            }

            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/v1/messages",  # Adjusted for Anthropic API
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=anthropic_request
            )

            result = response.json()

            # Convert Anthropic response to OpenAI format
            openai_response = {
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
                        "finish_reason": "stop"
                    }
                ]
            }

            # Record metrics
            response_time = time.time() - start_time
            tokens = (
                result.get("usage", {}).get("input_tokens", 0) +
                result.get("usage", {}).get("output_tokens", 0)
            )

            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Chat completion successful",
                           response_time=response_time,
                           tokens=tokens)

            return openai_response

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
        """Create a text completion using Anthropic's API"""
        # Anthropic primarily focuses on chat completions
        # We'll implement a basic version that converts the request
        start_time = time.time()

        try:
            # Convert text completion request to chat format
            prompt = request.get("prompt", "")
            anthropic_request = {
                "model": request.get("model"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "stream": request.get("stream", False)
            }

            # Make request with retry logic
            response = await self.make_request_with_retry(
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

            # Convert to text completion format
            text_completion_response = {
                "id": result.get("id"),
                "object": "text_completion",
                "created": int(time.time()),
                "model": result.get("model"),
                "choices": [
                    {
                        "text": result.get("content", [{}])[0].get("text", ""),
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": "stop"
                    }
                ]
            }

            # Record metrics
            response_time = time.time() - start_time
            tokens = (
                result.get("usage", {}).get("input_tokens", 0) +
                result.get("usage", {}).get("output_tokens", 0)
            )

            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Text completion successful",
                           response_time=response_time,
                           tokens=tokens)

            return text_completion_response

        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Text completion failed: {e}")
            raise

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Anthropic's API"""
        # Anthropic doesn't have a native embeddings API
        # We'll raise an exception indicating this feature is not supported
        raise NotImplementedError("Anthropic provider does not support embeddings")
