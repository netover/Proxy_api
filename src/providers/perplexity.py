"""
Perplexity.ai provider implementation
OpenAI-compatible API with real-time search capabilities
"""

import json
from typing import Union, AsyncGenerator
import time
from typing import Dict, Any, Optional, Union, AsyncGenerator
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from .base import Provider


class PerplexityProvider(Provider):
    """Perplexity.ai provider with OpenAI-compatible interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.perplexity.ai"
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _health_check(self) -> Dict[str, Any]:
        """Check Perplexity API health by making a minimal request"""
        try:
            # Try to get available models as health check
            response = await self.make_request_with_retry(
                "GET",
                f"{self.base_url}/models",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
            return {"models_available": len(response.json().get("data", []))}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"error": str(e)}

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion with Perplexity API with streaming support"""
        start_time = time.time()
 
        try:
            # Prepare request for Perplexity API
            perplexity_request = {
                "model": request.get("model", "sonar-pro"),
                "messages": request.get("messages", []),
                "max_tokens": request.get("max_tokens", 1024),
                "temperature": request.get("temperature", 0.7),
                "top_p": request.get("top_p", 1.0),
                "top_k": request.get("top_k", 0),
                "stream": request.get("stream", False),
                "presence_penalty": request.get("presence_penalty", 0.0),
                "frequency_penalty": request.get("frequency_penalty", 0.0)
            }
 
            # Add search parameters if model supports it
            model = request.get("model", "").lower()
            if "online" in model or "sonar" in model:
                perplexity_request["search_recency_filter"] = request.get("search_recency_filter", "month")
 
            if request.get('stream', False):
                # Streaming response
                async def stream_generator():
                    async with self.make_request_with_retry(
                        "POST",
                        f"{self.base_url}/chat/completions",
                        json=perplexity_request,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        stream=True
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                data = line[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    yield f"data: {json.dumps(chunk)}\n\n"
                                except json.JSONDecodeError:
                                    continue
                
                response_time = time.time() - start_time
                metrics_collector.record_request(
                    self.config.name,
                    success=True,
                    response_time=response_time,
                    tokens=0  # Tokens not available in streaming
                )
                self.logger.info("Chat completion streaming successful", response_time=response_time)
                return stream_generator()
            else:
                response = await self.make_request_with_retry(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    json=perplexity_request,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
 
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
        """Create text completion (mapped to chat completion for compatibility)"""
        # Convert text completion to chat completion format
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {
            **request,
            "messages": messages,
            "model": request.get("model", "sonar-pro")
        }
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Perplexity, return error)"""
        raise NotImplementedError("Perplexity.ai does not support embeddings. Use OpenAI or another provider for embeddings.")
