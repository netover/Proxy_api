from typing import Dict, Any
import httpx
from src.providers.base import Provider
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import time

class AnthropicProvider(Provider):
    """Anthropic provider implementation"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _health_check(self) -> Dict[str, Any]:
        """Check Anthropic health"""
        try:
            response = await self.make_request_with_retry(
                "GET",
                f"{self.config.base_url}/v1/models",
                headers={"x-api-key": self.api_key}
            )
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a chat completion using Anthropic's API"""
        start_time = time.time()

        try:
            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.config.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json=request
            )

            result = response.json()

            # Record metrics
            response_time = time.time() - start_time
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)
            tokens = input_tokens + output_tokens

            metrics_collector.record_request(
                self.config.name,
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
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Chat completion failed: {e}")
            raise

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a text completion using Anthropic's API"""
        # Anthropic doesn't have a separate text completion endpoint like OpenAI
        # We'll use the messages endpoint with a system prompt
        start_time = time.time()

        try:
            # Convert OpenAI-style request to Anthropic format
            anthropic_request = {
                "model": request.get("model", "claude-3-sonnet-20240229"),
                "max_tokens": request.get("max_tokens", 1000),
                "messages": [
                    {
                        "role": "user",
                        "content": request.get("prompt", "")
                    }
                ]
            }

            # Make request with retry logic
            response = await self.make_request_with_retry(
                "POST",
                f"{self.config.base_url}/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json=anthropic_request
            )

            result = response.json()

            # Record metrics
            response_time = time.time() - start_time
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)
            tokens = input_tokens + output_tokens

            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )

            self.logger.info("Text completion successful",
                           response_time=response_time,
                           tokens=tokens)

            # Convert back to OpenAI-style response format
            content = result.get("content", [])
            if isinstance(content, list) and content:
                content = content[0]
            else:
                content = {}
            if not isinstance(content, dict):
                content = {}
            
            return {
                "id": result.get("id", ""),
                "object": "text_completion",
                "created": int(time.time()),
                "model": result.get("model", ""),
                "choices": [
                    {
                        "text": content.get("text", ""),
                        "index": 0,
                        "logprobs": None,
                        "finish_reason": result.get("stop_reason", "stop")
                    }
                ],
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": tokens
                }
            }

        except Exception as e:
            response_time = time.time() - start_time

            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )

            self.logger.error(f"Text completion failed: {e}")
            raise

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Anthropic's API"""
        # Anthropic doesn't have a native embeddings endpoint
        # This is a placeholder - would need to use a different service
        raise NotImplementedError("Anthropic does not provide embeddings API")
