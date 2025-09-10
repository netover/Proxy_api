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

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], async_generator]:
        """Create chat completion using OpenAI API with streaming support"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                async with self.make_request(
                    "POST",
                    f"{self.config.base_url}/chat/completions",
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
                f"{self.config.base_url}/chat/completions",
                json=request,
                headers=headers
            )
            data = response.json()
            
            # Specific error handling
            if 'error' in data:
                error = data['error']
                if error['type'] == 'invalid_request_error':
                    raise ValueError(f"OpenAI Invalid Request: {error['message']}")
                elif error['type'] == 'rate_limit_error':
                    raise Exception(f"OpenAI Rate Limit: {error['message']}")
                else:
                    raise Exception(f"OpenAI Error: {error['message']}")
            
            # Handle usage
            if 'usage' in data:
                data['usage'] = {
                    'prompt_tokens': data['usage']['prompt_tokens'],
                    'completion_tokens': data['usage']['completion_tokens'],
                    'total_tokens': data['usage']['total_tokens']
                }
            
            return data

    async def create_text_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], async_generator]:
        """Create text completion using OpenAI API with streaming support"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                async with self.make_request(
                    "POST",
                    f"{self.config.base_url}/completions",
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
                f"{self.config.base_url}/completions",
                json=request,
                headers=headers
            )
            data = response.json()
            
            # Specific error handling
            if 'error' in data:
                error = data['error']
                if error['type'] == 'invalid_request_error':
                    raise ValueError(f"OpenAI Invalid Request: {error['message']}")
                elif error['type'] == 'rate_limit_error':
                    raise Exception(f"OpenAI Rate Limit: {error['message']}")
                else:
                    raise Exception(f"OpenAI Error: {error['message']}")
            
            # Handle usage
            if 'usage' in data:
                data['usage'] = {
                    'prompt_tokens': data['usage']['prompt_tokens'],
                    'completion_tokens': data['usage']['completion_tokens'],
                    'total_tokens': data['usage']['total_tokens']
                }
            
            return data

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI API"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = await self.make_request(
            "POST",
            f"{self.config.base_url}/embeddings",
            json=request,
            headers=headers
        )
        data = response.json()
        
        # Specific error handling
        if 'error' in data:
            error = data['error']
            if error['type'] == 'invalid_request_error':
                raise ValueError(f"OpenAI Invalid Request: {error['message']}")
            elif error['type'] == 'rate_limit_error':
                raise Exception(f"OpenAI Rate Limit: {error['message']}")
            else:
                raise Exception(f"OpenAI Error: {error['message']}")
        
        return data
