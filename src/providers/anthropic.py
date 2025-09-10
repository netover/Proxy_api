from typing import Dict, Any, Union, AsyncGenerator
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
import json

class AnthropicProvider(BaseProvider):
    """Anthropic API provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Health check for Anthropic API"""
        try:
            response = await self.make_request(
                "GET", f"{self.config.base_url}/v1/models",
                headers={"x-api-key": self.api_key}
            )
            return {
                "healthy": response.status_code == 200,
                "details": {"status_code": response.status_code}
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion using Anthropic API with streaming support"""
        headers = {"x-api-key": self.api_key}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                async with self.make_request(
                    "POST",
                    f"{self.config.base_url}/v1/messages",
                    json=request,
                    headers=headers,
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
            
            return stream_generator()
        else:
            # Non-streaming
            response = await self.make_request(
                "POST",
                f"{self.config.base_url}/v1/messages",
                json=request,
                headers=headers
            )
            return response.json()

    async def create_text_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create text completion using Anthropic API with streaming support"""
        # Anthropic doesn't have separate text completion, use messages
        messages = [{"role": "user", "content": request.get("prompt", "")}]
        request["messages"] = messages
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Anthropic does not support embeddings"""
        raise NotImplementedError("Anthropic API does not support embeddings")
