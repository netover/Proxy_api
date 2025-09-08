"""
Blackbox.ai provider implementation
Unified API for chat, image, video, and tool calling
"""

import json
from typing import Dict, Any, Optional
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from .base import Provider


class BlackboxProvider(Provider):
    """Blackbox.ai provider with unified API interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.blackbox.ai"
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _health_check(self) -> Dict[str, Any]:
        """Check Blackbox API health"""
        try:
            # Try to get available models as health check
            response = await self.make_request_with_retry(
                "GET",
                f"{self.base_url}/v1/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            return {"models_available": len(response.json().get("data", []))}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with Blackbox API"""
        start_time = __import__('time').time()

        try:
            # Prepare request for Blackbox API
            blackbox_request = {
                "model": request.get("model", "blackbox-chat"),
                "messages": request.get("messages", []),
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "top_p": request.get("top_p", 1.0),
                "stream": request.get("stream", False),
                "tools": request.get("tools", []),
                "tool_choice": request.get("tool_choice", None)
            }

            # Determine endpoint based on request type
            endpoint = "/v1/chat/completions"
            if request.get("tools"):
                endpoint = "/v1/chat/completions/tool"

            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}{endpoint}",
                json=blackbox_request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()
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

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {
            **request,
            "messages": messages,
            "model": request.get("model", "blackbox-chat")
        }
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Blackbox, return error)"""
        raise NotImplementedError("Blackbox.ai does not support embeddings. Use OpenAI or another provider for embeddings.")

    async def create_image(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create image generation with Blackbox API"""
        start_time = __import__('time').time()

        try:
            image_request = {
                "model": request.get("model", "blackbox-image"),
                "prompt": request.get("prompt", ""),
                "size": request.get("size", "1024x1024"),
                "quality": request.get("quality", "standard"),
                "n": request.get("n", 1)
            }

            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/v1/image/generations",
                json=image_request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()
            response_time = __import__('time').time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=0  # Images don't use tokens in the same way
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

    async def create_video(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create video generation with Blackbox API"""
        start_time = __import__('time').time()

        try:
            video_request = {
                "model": request.get("model", "blackbox-video"),
                "prompt": request.get("prompt", ""),
                "duration": request.get("duration", 5),
                "resolution": request.get("resolution", "720p")
            }

            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/v1/video/generations",
                json=video_request,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )

            result = response.json()
            response_time = __import__('time').time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=0  # Videos don't use tokens in the same way
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
