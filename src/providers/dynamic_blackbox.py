from typing import Dict, Any, Union, AsyncGenerator
import asyncio
import json
from src.providers.dynamic_base import DynamicProvider
from src.core.metrics import metrics_collector
import time

class DynamicBlackboxProvider(DynamicProvider):
    """Dynamic Blackbox.ai provider implementation"""

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Check Blackbox API health"""
        try:
            response = await self.make_request(
                "GET",
                f"{self.base_url}/v1/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            return {"models_available": len(response.json().get("data", []))}
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Create chat completion with Blackbox API with streaming support"""
        start_time = time.time()
        stream = request.get('stream', False)
        try:
            if stream:
                async def stream_generator():
                    try:
                        response = await self.make_request(
                            "POST",
                            f"{self.base_url}/v1/chat/completions",
                            json=request,
                            stream=True,
                            headers={
                                "Authorization": f"Bearer {self.api_key}",
                                "Content-Type": "application/json"
                            }
                        )
                        async with response:
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
                    except Exception as e:
                        self.logger.error(f"Streaming completion failed: {e}")
                        raise
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
                response = await self.make_request(
                    "POST",
                    f"{self.base_url}/v1/chat/completions",
                    json=request,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                result = response.json()
                response_time = time.time() - start_time
                metrics_collector.record_request(
                    self.name,
                    success=True,
                    response_time=response_time,
                    tokens=result.get("usage", {}).get("total_tokens", 0)
                )
                return result
        except Exception as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            self.logger.error(f"Chat completion failed: {e}")
            raise

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion (mapped to chat completion)"""
    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Blackbox)"""
        raise NotImplementedError("Blackbox provider does not support embeddings")
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        chat_request = {**request, "messages": messages}
        return await self.create_completion(chat_request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings (not supported by Blackbox)"""
        raise NotImplementedError("Blackbox.ai does not support embeddings.")
