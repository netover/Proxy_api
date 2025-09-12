from typing import Dict, Any, Optional, Set
"""
Blackbox.ai provider implementation
Unified API for chat, image, video, and tool calling
"""

import json
import time
from typing import Dict, Any, Optional
import httpx
from src.core.unified_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from src.core.provider_factory import BaseProvider, ProviderCapability
from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError


class BlackboxProvider(BaseProvider):
    """Blackbox.ai provider with unified API interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.blackbox.ai"
        self.logger = ContextualLogger(f"provider.{config.name}")
        self.logger = ContextualLogger(f"provider.{config.name}")

    def _get_capabilities(self) -> Set[ProviderCapability]:
        """Get Blackbox provider capabilities"""
        from src.core.provider_factory import ProviderCapability
        capabilities = super()._get_capabilities()

        # Blackbox doesn't support embeddings
        capabilities.discard(ProviderCapability.EMBEDDINGS)

        # Blackbox supports image and video generation
        capabilities.add(ProviderCapability.IMAGE_GENERATION)
        capabilities.add(ProviderCapability.VIDEO_GENERATION)

        return capabilities

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Blackbox API health"""
        try:
            # Try to get available models as health check
            response = await self.make_request(
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

    def _validate_completion_request(self, request: Dict[str, Any]):
        """Validate chat completion request"""
        if not request.get("model"):
            raise InvalidRequestError("Missing required 'model' parameter", param="model", code="missing_model")
        if not request.get("messages"):
            raise InvalidRequestError("Missing required 'messages' parameter", param="messages", code="missing_messages")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    def _validate_image_request(self, request: Dict[str, Any]):
        """Validate image generation request"""
        if not request.get("model"):
            raise InvalidRequestError("Missing required 'model' parameter (e.g., blackbox-image-1)", param="model", code="missing_model")
        if not request.get("prompt"):
            raise InvalidRequestError("Missing required 'prompt' parameter", param="prompt", code="missing_prompt")

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with Blackbox API"""
        self._validate_completion_request(request)
        start_time = time.time()

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

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = await self.make_request(
                "POST",
                f"{self.base_url}{endpoint}",
                json=blackbox_request,
                headers=headers
            )

            # Error handling
            if response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif response.status_code == 400:
                error_data = response.text
                raise InvalidRequestError(f"Blackbox Invalid Request: {error_data}", code="invalid_request")

            result = response.json()
            response_time = time.time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=result.get("usage", {}).get("total_tokens", 0)
            )

            return result

        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            if e.response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Blackbox Invalid Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"Blackbox API error: {e.response.status_code}", code="api_error")
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise APIConnectionError(f"Blackbox Connection error: {str(e)}", code="connection_error")

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
        self._validate_image_request(request)
        start_time = time.time()

        try:
            image_request = {
                "model": request.get("model", "blackbox-image-1"),
                "prompt": request.get("prompt", ""),
                "size": request.get("size", "1024x1024"),
                "quality": request.get("quality", "standard"),
                "n": request.get("n", 1)
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/images/generations",
                json=image_request,
                headers=headers
            )

            # Error handling
            if response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif response.status_code == 400:
                error_data = response.text
                raise InvalidRequestError(f"Blackbox Invalid Image Request: {error_data}", code="invalid_request")

            result = response.json()
            response_time = time.time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=0  # Images don't use tokens in the same way
            )

            return result

        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            if e.response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Blackbox Invalid Image Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"Blackbox Image API error: {e.response.status_code}", code="api_error")
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise APIConnectionError(f"Blackbox Image Connection error: {str(e)}", code="connection_error")

    async def create_video(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create video generation with Blackbox API"""
        start_time = time.time()

        try:
            video_request = {
                "model": request.get("model", "blackbox-video"),
                "prompt": request.get("prompt", ""),
                "duration": request.get("duration", 5),
                "resolution": request.get("resolution", "720p")
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/video/generations",
                json=video_request,
                headers=headers
            )

            # Error handling
            if response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif response.status_code == 400:
                error_data = response.text
                raise InvalidRequestError(f"Blackbox Invalid Video Request: {error_data}", code="invalid_request")

            result = response.json()
            response_time = time.time() - start_time

            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=0  # Videos don't use tokens in the same way
            )

            return result

        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            if e.response.status_code == 401:
                raise AuthenticationError("Blackbox Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("Blackbox Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Blackbox Invalid Video Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"Blackbox Video API error: {e.response.status_code}", code="api_error")
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise APIConnectionError(f"Blackbox Video Connection error: {str(e)}", code="connection_error")
