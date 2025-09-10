"""
Grok (xAI) provider implementation
Uses xAI SDK with OpenAI-compatible interface
"""

import json
import time
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
        # Add Authorization header for Grok API
        self.client.headers.update({"Authorization": f"Bearer {self.api_key}"})

    async def _health_check(self) -> Dict[str, Any]:
        """Check Grok API health"""
        try:
            response = await self.client.get(f"{self.base_url}/models")
            response.raise_for_status()
            return {"status": "healthy"}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with Grok API"""
        start_time = time.time()

        try:
            # Extract parameters
            model = request.get("model", "grok-beta")
            messages = request.get("messages", [])
            max_tokens = request.get("max_tokens", 1024)
            temperature = request.get("temperature", 0.7)
            top_p = request.get("top_p", 1.0)
            stream = request.get("stream", False)

            # Prepare request body (OpenAI compatible)
            body = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stream": stream
            }

            # Make request using httpx
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=body
            )
            response.raise_for_status()
            result = response.json()
            response_time = time.time() - start_time

            # Record metrics
            usage = result.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=total_tokens
            )

            return result

        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise




    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {
            **request,
            "messages": messages,
            "model": request.get("model", "grok-beta")
        }
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Grok, return error)"""
        raise NotImplementedError("Grok (xAI) does not support embeddings. Use OpenAI or another provider for embeddings.")
