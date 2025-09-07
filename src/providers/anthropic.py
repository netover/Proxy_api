from typing import Dict, Any
import httpx
from src.providers.base import Provider
from src.core.app_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
import time

class AnthropicProvider(Provider):
    """Anthropic provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.logger = ContextualLogger(f"provider.{config.name}")
        
    async def _health_check(self) -> Dict[str, Any]:
        """Check Anthropic health"""
        try:
            response = await self.client.get(
                f"{self.config.base_url}/v1/models",
                headers={"x-api-key": self.api_key}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            raise
    
    async def create_completion(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a completion using Anthropic's API"""
        start_time = time.time()
        
        try:
            # Prepare request
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Make request
            response = await self.client.post(
                f"{self.config.base_url}/v1/messages",
                headers=headers,
                json=request
            )
            
            response.raise_for_status()
            
            # Record metrics
            response_time = time.time() - start_time
            # Anthropic doesn't return token count in the same way as OpenAI
            # We'll estimate based on input/output
            input_tokens = response.json().get("usage", {}).get("input_tokens", 0)
            output_tokens = response.json().get("usage", {}).get("output_tokens", 0)
            tokens = input_tokens + output_tokens
            
            metrics_collector.record_request(
                self.config.name,
                success=True,
                response_time=response_time,
                tokens=tokens
            )
            
            self.logger.info(f"Completion successful", 
                           response_time=response_time, 
                           tokens=tokens)
            
            return response.json()
            
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=f"http_{e.response.status_code}"
            )
            
            self.logger.error(f"HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            response_time = time.time() - start_time
            
            metrics_collector.record_request(
                self.config.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            
            self.logger.error(f"Request failed: {e}")
            raise
