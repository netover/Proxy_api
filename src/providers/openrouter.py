"""
OpenRouter provider implementation
Unified endpoint for 280+ models from multiple providers
OpenAI-compatible schema with 5-min in-memory cache for models
"""

import json
import time
import asyncio
from typing import Dict, Any, Optional
import httpx
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from .base import Provider
from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError


class OpenRouterProvider(Provider):
    """OpenRouter provider with unified model access"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://openrouter.ai/api"
        self.logger = ContextualLogger(f"provider.{config.name}")
        self._models_cache = None
        self._models_cache_time = 0
        self._cache_ttl = 300  # 5 minutes
        self._lock = asyncio.Lock()

    async def _health_check(self) -> Dict[str, Any]:
        """Check OpenRouter API health"""
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
            models_data = response.json()
            return {
                "models_available": len(models_data.get("data", [])),
                "providers": len(set(model.get("id", "").split("/")[0] for model in models_data.get("data", [])))
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    def _validate_request(self, request: Dict[str, Any]):
        """Validate required parameters for OpenRouter requests"""
        if not request.get('model'):
            raise InvalidRequestError("Missing required 'model' parameter", param="model", code="missing_model")
        if not request.get('messages') and not request.get('prompt'):
            raise InvalidRequestError("Missing required 'messages' or 'prompt' parameter", code="missing_input")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    async def _get_models(self) -> Dict[str, Any]:
        """Get available models with 5-min in-memory caching"""
        current_time = time.time()

        async with self._lock:
            if self._models_cache and (current_time - self._models_cache_time) < self._cache_ttl:
                return self._models_cache

            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                response = await self.make_request_with_retry(
                    "GET",
                    f"{self.base_url}/v1/models",
                    headers=headers
                )

                # Error handling for models fetch
                if response.status_code == 401:
                    raise AuthenticationError("OpenRouter Authentication failed for models", code="unauthorized")
                elif response.status_code == 429:
                    raise RateLimitError("OpenRouter Rate limit for models", code="rate_limit")
                elif response.status_code == 400:
                    raise InvalidRequestError(f"OpenRouter Invalid Request for models: {response.text}", code="invalid_request")

                self._models_cache = response.json()
                self._models_cache_time = current_time
                return self._models_cache

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AuthenticationError("OpenRouter Authentication failed for models", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("OpenRouter Rate limit for models", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"OpenRouter Invalid Request for models: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"OpenRouter Models API error: {e.response.status_code}", code="api_error")
            except Exception as e:
                self.logger.error(f"Failed to fetch models: {e}")
                return {"data": []}

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion with OpenRouter API (OpenAI-compatible)"""
        self._validate_request(request)
        start_time = time.time()

        try:
            # Prepare request for OpenRouter API
            openrouter_request = {
                "model": request.get("model", "openai/gpt-3.5-turbo"),
                "messages": request.get("messages", []),
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "top_p": request.get("top_p", 1.0),
                "top_k": request.get("top_k"),
                "frequency_penalty": request.get("frequency_penalty", 0.0),
                "presence_penalty": request.get("presence_penalty", 0.0),
                "repetition_penalty": request.get("repetition_penalty", 1.0),
                "stop": request.get("stop"),
                "logit_bias": request.get("logit_bias"),
                "logprobs": request.get("logprobs"),
                "response_format": request.get("response_format"),
                "tools": request.get("tools"),
                "tool_choice": request.get("tool_choice"),
                "parallel_tool_calls": request.get("parallel_tool_calls"),
                "stream": request.get("stream", False)
            }

            # Remove None values
            openrouter_request = {k: v for k, v in openrouter_request.items() if v is not None}

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": request.get("extra_body", {}).get("referer", ""),
                "X-Title": request.get("extra_body", {}).get("title", "")
            }
            response = await self.make_request_with_retry(
                "POST",
                f"{self.base_url}/v1/chat/completions",
                json=openrouter_request,
                headers=headers
            )

            # Error handling
            if response.status_code == 401:
                raise AuthenticationError("OpenRouter Authentication failed", code="unauthorized")
            elif response.status_code == 429:
                raise RateLimitError("OpenRouter Rate limit exceeded", code="rate_limit")
            elif response.status_code == 400:
                error_data = response.text
                raise InvalidRequestError(f"OpenRouter Invalid Request: {error_data}", code="invalid_request")

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
                raise AuthenticationError("OpenRouter Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("OpenRouter Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"OpenRouter Invalid Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"OpenRouter API error: {e.response.status_code}", code="api_error")
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise APIConnectionError(f"OpenRouter Connection error: {str(e)}", code="connection_error")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
        self._validate_request(request)
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {
            **request,
            "messages": messages,
            "model": request.get("model", "openai/gpt-3.5-turbo")
        }
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by OpenRouter, return error)"""
        raise NotImplementedError("OpenRouter does not support embeddings. Use OpenAI or another provider for embeddings.")

    async def list_models(self) -> Dict[str, Any]:
        """List all available models from OpenRouter (cached)"""
        return await self._get_models()
