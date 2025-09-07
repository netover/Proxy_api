from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import httpx
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import os

class Provider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.api_key = os.getenv(config.api_key_env, "")
        self.logger = ContextualLogger(f"provider.{config.name}")
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={"User-Agent": "LLM-Proxy-API/1.0"}
        )
        
        if not self.api_key:
            self.logger.warning(f"API key for {config.name} not found in environment")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        start_time = time.time()
        try:
            result = await self._health_check()
            response_time = time.time() - start_time
            
            metrics_collector.record_request(
                self.config.name, 
                success=True, 
                response_time=response_time,
                error_type=None
            )
            
            return {
                "status": "healthy" if result else "unhealthy",
                "response_time": response_time,
                "details": result
            }
        except Exception as e:
            response_time = time.time() - start_time
            
            metrics_collector.record_request(
                self.config.name, 
                success=False, 
                response_time=response_time,
                error_type=type(e).__name__
            )
            
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "error": str(e)
            }
    
    @abstractmethod
    async def _health_check(self) -> Any:
        """Internal health check implementation"""
        pass
    
    @abstractmethod
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a completion using the provider's API"""
        pass
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# Import implementations after base class
from src.providers.openai import OpenAIProvider
from src.providers.anthropic import AnthropicProvider

# Provider factory
PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider
}

def get_provider(config: ProviderConfig) -> Provider:
    """Factory function to get provider instance"""
    provider_class = PROVIDER_CLASSES.get(config.type.lower())
    if not provider_class:
        raise ValueError(f"Unsupported provider type: {config.type}")
    return provider_class(config)
