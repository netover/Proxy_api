from typing import Dict, Any
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig

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

    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create chat completion using Anthropic API"""
        headers = {"x-api-key": self.api_key}
        response = await self.make_request(
            "POST",
            f"{self.config.base_url}/v1/messages",
            json=request,
            headers=headers
        )
        return response.json()

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion using Anthropic API"""
        # Anthropic doesn't have separate text completion, use messages
        messages = [{"role": "user", "content": request["prompt"]}]
        request["messages"] = messages
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Anthropic does not support embeddings"""
        raise NotImplementedError("Anthropic API does not support embeddings")
