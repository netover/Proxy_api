from typing import Dict, Any
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Health check for OpenAI API"""
        try:
            response = await self.make_request(
                "GET", f"{self.config.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"}
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
        """Create chat completion using OpenAI API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.make_request(
            "POST",
            f"{self.config.base_url}/chat/completions",
            json=request,
            headers=headers
        )
        return response.json()

    async def create_text_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create text completion using OpenAI API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.make_request(
            "POST",
            f"{self.config.base_url}/completions",
            json=request,
            headers=headers
        )
        return response.json()

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.make_request(
            "POST",
            f"{self.config.base_url}/embeddings",
            json=request,
            headers=headers
        )
        return response.json()
