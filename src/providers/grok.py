"""
Grok (xAI) provider implementation
Uses /v1/complete endpoint with prompt-based payload per official docs
No streaming support; limitations: grok-beta model, no embeddings
"""

import time
from typing import Any, Dict

import httpx

from src.core.exceptions import (APIConnectionError, AuthenticationError,
                                 InvalidRequestError, RateLimitError)
from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig


class GrokProvider(BaseProvider):
    """Grok (xAI) provider with /v1/complete interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Health check for Grok API using GET /v1/models"""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = await self.make_request(
                "GET",
                f"{self.config.base_url}/v1/models",
                headers=headers
            )
            return {
                "healthy": response.status_code == 200,
                "details": {"status_code": response.status_code, "models": response.json().get('data', [])}
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    def _validate_request(self, request: Dict[str, Any]):
        """Validate required parameters for Grok requests"""
        if not request.get('model'):
            raise InvalidRequestError("Missing required 'model' parameter (e.g., grok-beta)", param="model", code="missing_model")
        if not request.get('messages') and not request.get('prompt'):
            raise InvalidRequestError("Missing required 'messages' or 'prompt' parameter", code="missing_input")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    def _transform_to_prompt(self, request: Dict[str, Any]) -> str:
        """Transform messages or prompt to single prompt string"""
        if request.get('messages'):
            messages = request.get('messages', [])
            prompt_parts = []
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                prompt_parts.append(f"{role.capitalize()}: {content}")
            return "\n".join(prompt_parts)
        else:
            return request.get('prompt', '')

    def _parse_response(self, grok_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Grok /v1/complete response to OpenAI-compatible format"""
        choices = grok_response.get('choices', [])
        if not choices:
            raise APIConnectionError("No choices in Grok response", code="no_choices")
        
        text = choices[0].get('text', '')
        return {
            "id": grok_response.get('id', ''),
            "object": "chat.completion" if request.get('messages') else "text_completion",
            "created": int(time.time()),
            "model": grok_response.get('model', ''),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                } if request.get('messages') else {"text": text},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": grok_response.get('usage', {}).get('prompt_tokens', 0),
                "completion_tokens": grok_response.get('usage', {}).get('completion_tokens', 0),
                "total_tokens": grok_response.get('usage', {}).get('total_tokens', 0)
            }
        }

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion using Grok /v1/complete (no streaming)"""
        self._validate_request(request)
        start_time = time.time()
        try:
            prompt = self._transform_to_prompt(request)
            if not prompt:
                raise InvalidRequestError("Empty prompt after transformation", code="empty_prompt")
            
            grok_request = {
                "model": request.get("model", "grok-beta"),
                "prompt": prompt,
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "top_p": request.get("top_p", 1.0)
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = await self.make_request(
                "POST",
                f"{self.config.base_url}/v1/complete",
                json=grok_request,
                headers=headers
            )
            
            # Error handling
            if response.status_code == 401:
                raise AuthenticationError("Grok Authentication failed", code="unauthorized")
            elif response.status_code == 429:
                raise RateLimitError("Grok Rate limit exceeded", code="rate_limit")
            elif response.status_code == 400:
                error_data = response.text
                raise InvalidRequestError(f"Grok Invalid Request: {error_data}", code="invalid_request")
            
            result = response.json()
            response_time = time.time() - start_time
            
            # Record metrics
            usage = result.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=total_tokens
            )
            self.logger.info("Completion successful", response_time=response_time, tokens=total_tokens)
            
            return self._parse_response(result)
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            if e.response.status_code == 401:
                raise AuthenticationError("Grok Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("Grok Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Grok Invalid Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"Grok API error: {e.response.status_code}", code="api_error")
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            raise APIConnectionError(f"Grok Connection error: {str(e)}", code="connection_error")

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion using Grok /v1/complete directly"""
        self._validate_request(request)
        request['prompt'] = request.get('prompt', '')  # Ensure prompt
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Grok, return error)"""
        raise NotImplementedError("Grok (xAI) does not support embeddings. Limitation: Use OpenAI or another provider.")
