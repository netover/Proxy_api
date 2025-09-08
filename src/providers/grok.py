"""
Grok (xAI) provider implementation
Uses xAI SDK with OpenAI-compatible interface
"""

import json
from typing import Dict, Any, Optional
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from .base import Provider


class GrokProvider(Provider):
    """Grok (xAI) provider with OpenAI-compatible interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.x.ai/v1"
        self.logger = ContextualLogger(f"provider.{config.name}")

        # Import xAI SDK if available
        try:
            import xai_sdk
            self.xai_client = xai_sdk.Client(api_key=self.api_key)
            self.sdk_available = True
        except ImportError:
            self.logger.warning("xAI SDK not available. Install with: pip install xai-sdk")
            self.sdk_available = False
            self.xai_client = None

    async def _health_check(self) -> Dict[str, Any]:
        """Check Grok API health"""
        if not self.sdk_available:
            return {"error": "xAI SDK not available"}

        try:
            # Simple health check by attempting to get model info
            # Note: This is a placeholder - actual implementation depends on SDK
            return {"status": "healthy", "sdk_available": True}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with Grok API"""
        start_time = __import__('time').time()

        if not self.sdk_available:
            raise RuntimeError("xAI SDK not available. Install with: pip install xai-sdk")

        try:
            # Extract parameters
            model = request.get("model", "grok-4")
            messages = request.get("messages", [])
            max_tokens = request.get("max_tokens", 1024)
            temperature = request.get("temperature", 0.7)
            stream = request.get("stream", False)

            # Convert messages to xAI format
            prompt = self._convert_messages_to_prompt(messages)

            # Prepare xAI request
            xai_request = {
                "model": model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": stream
            }

            # Add search parameters if enabled
            if request.get("extra_body", {}).get("search_enabled", False):
                xai_request["search_parameters"] = {
                    "max_search_results": request.get("extra_body", {}).get("search_parameters", {}).get("max_search_results", 5)
                }
                xai_request["include_citations"] = request.get("extra_body", {}).get("include_citations", True)
                xai_request["search_timeout"] = request.get("extra_body", {}).get("search_timeout", 10)

            # Make request using xAI SDK
            # Note: This is a placeholder - actual implementation depends on SDK methods
            response = await self._make_xai_request(xai_request)

            # Convert xAI response to OpenAI format
            result = self._convert_xai_response_to_openai(response)
            response_time = __import__('time').time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=result.get("usage", {}).get("total_tokens", 0)
            )

            return result

        except Exception as e:
            response_time = __import__('time').time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise

    async def _make_xai_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to xAI API using SDK"""
        # Placeholder - actual implementation depends on xAI SDK
        # This would use the xAI SDK methods
        if self.xai_client:
            # Example: response = await self.xai_client.generate(request_data)
            # For now, return mock response
            return {
                "choices": [{"message": {"content": "Mock Grok response"}}],
                "usage": {"total_tokens": 100}
            }
        else:
            raise RuntimeError("xAI client not initialized")

    def _convert_messages_to_prompt(self, messages: list) -> str:
        """Convert OpenAI message format to xAI prompt format"""
        prompt_parts = []
        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        return "\n\n".join(prompt_parts)

    def _convert_xai_response_to_openai(self, xai_response: Dict[str, Any]) -> Dict[str, Any]:
        """Convert xAI response to OpenAI format"""
        return {
            "id": f"grok-{__import__('time').time()}",
            "object": "chat.completion",
            "created": int(__import__('time').time()),
            "model": "grok-4",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": xai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
                },
                "finish_reason": "stop"
            }],
            "usage": xai_response.get("usage", {"total_tokens": 0})
        }

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {
            **request,
            "messages": messages,
            "model": request.get("model", "grok-4")
        }
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Grok, return error)"""
        raise NotImplementedError("Grok (xAI) does not support embeddings. Use OpenAI or another provider for embeddings.")
