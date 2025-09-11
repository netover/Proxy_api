"""
Perplexity.ai provider implementation
Uses /v1/ask endpoint for search-enabled completions
No streaming support
"""

import json
import time
from typing import Dict, Any
import httpx
from src.core.unified_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from .base import Provider
from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError


class PerplexityProvider(Provider):
    """Perplexity.ai provider with /v1/ask interface mapped to OpenAI-compatible"""
 
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.perplexity.ai"
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Perplexity API health using /v1/models"""
        try:
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

    def _validate_request(self, request: Dict[str, Any]):
        """Validate required parameters for Perplexity requests"""
        if not request.get('model'):
            raise InvalidRequestError("Missing required 'model' parameter", param="model", code="missing_model")
        if not request.get('messages') and not request.get('prompt'):
            raise InvalidRequestError("Missing required 'messages' or 'prompt' parameter", code="missing_input")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    def _transform_to_ask(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform OpenAI request to Perplexity /v1/ask payload"""
        # Extract query from last user message or prompt
        if request.get('messages'):
            messages = request.get('messages', [])
            query = next((msg['content'] for msg in reversed(messages) if msg['role'] == 'user'), '')
        else:
            query = request.get('prompt', '')
        
        ask_request = {
            "model": request.get("model", "llama-3.1-sonar-small-128k-online"),
            "query": query,
            "max_tokens": request.get("max_tokens", 1024),
            "temperature": request.get("temperature", 0.7),
            "top_p": request.get("top_p", 0.9)
        }
        return ask_request

    def _parse_ask_response(self, ask_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse /v1/ask response to OpenAI-compatible format"""
        answers = ask_response.get('answers', [])
        if not answers:
            raise APIConnectionError("No answers in Perplexity response", code="no_answers")
        
        # Take first answer as main completion, include sources
        answer = answers[0]
        sources = answer.get('sources', [])
        source_info = [{"title": s.get('title', ''), "url": s.get('url', ''), "snippet": s.get('snippet', '')} for s in sources]
        
        return {
            "id": ask_response.get('id', ''),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": ask_response.get('model', ''),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": answer.get('text', '')
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": ask_response.get('request_tokens', 0),
                "completion_tokens": ask_response.get('response_tokens', 0),
                "total_tokens": ask_response.get('request_tokens', 0) + ask_response.get('response_tokens', 0)
            },
            "perplexity_sources": source_info  # Extra field for sources
        }

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion using Perplexity /v1/ask (no streaming)"""
        self._validate_request(request)
        start_time = time.time()
        try:
            ask_request = self._transform_to_ask(request)
            headers = {
                "x-perplexity-api-key": self.api_key,  # Use header as per docs
                "Content-Type": "application/json"
            }
            response = await self.make_request(
                "POST",
                f"{self.base_url}/v1/ask",
                json=ask_request,
                headers=headers
            )
            result = response.json()
            response_time = time.time() - start_time
            
            # Record metrics
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=result.get("request_tokens", 0) + result.get("response_tokens", 0)
            )
            self.logger.info("Ask completion successful", response_time=response_time)
            
            # Parse to OpenAI format
            return self._parse_ask_response(result)
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
        """Create text completion synonym for create_completion (uses /v1/ask)"""
        self._validate_request(request)
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Perplexity, return error)"""
        raise NotImplementedError("Perplexity.ai does not support embeddings. Use OpenAI or another provider for embeddings.")
