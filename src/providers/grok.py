"""
Grok (xAI) provider implementation
Uses xAI SDK with OpenAI-compatible interface
"""

from typing import Dict, Any, Union, AsyncGenerator
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
import json
import json
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import time

class GrokProvider(BaseProvider):
    """Grok (xAI) provider with OpenAI-compatible interface"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Grok API health"""
        try:
            response = await self.make_request(
                "GET", f"{self.config.base_url}/models"
            )
            response.raise_for_status()
            return {
                "healthy": True,
                "details": {"status_code": response.status_code}
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion with Grok API with streaming support"""
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
 
            if stream:
                # Streaming response
                async def stream_generator():
                    async with self.make_request(
                        "POST",
                        f"{self.config.base_url}/chat/completions",
                        json=body,
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
                    self.name,
                    success=True,
                    response_time=response_time,
                    tokens=0  # Tokens not available in streaming
                )
                self.logger.info("Chat completion streaming successful", response_time=response_time)
                return stream_generator()
            else:
                # Non-streaming
                response = await self.make_request(
                    "POST",
                    f"{self.config.base_url}/chat/completions",
                    json=body
                )
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
 
                self.logger.info("Chat completion successful",
                                 response_time=response_time,
                                 tokens=total_tokens)
 
                return result
 
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
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
