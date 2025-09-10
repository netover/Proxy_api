from typing import Dict, Any, Union, AsyncGenerator
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
import json

from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError

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

    def _validate_request(self, request: Dict[str, Any], is_chat: bool = True):
        """Validate required parameters for OpenAI requests"""
        required = ['model']
        if is_chat:
            required.append('messages')
            if not request.get('messages'):
                raise InvalidRequestError("Missing required 'messages' parameter", param="messages", code="missing_messages")
        else:
            required.append('prompt')
            if not request.get('prompt'):
                raise InvalidRequestError("Missing required 'prompt' parameter", param="prompt", code="missing_prompt")
        
        for field in required:
            if field not in request or not request[field]:
                raise InvalidRequestError(f"Missing required parameter: {field}", param=field, code=f"missing_{field}")
        
        # Optional but common params can have defaults, but validate types if present
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion using OpenAI API with streaming support"""
        self._validate_request(request, is_chat=True)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                try:
                    async with self.make_request(
                        "POST",
                        f"{self.config.base_url}/chat/completions",
                        json=request,
                        headers=headers,
                        stream=True
                    ) as response:
                        if response.status_code == 401:
                            raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                        elif response.status_code == 429:
                            raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                        elif response.status_code == 400:
                            error_data = await response.aread()
                            try:
                                error_json = json.loads(error_data)
                                raise InvalidRequestError(error_json['error']['message'], code=error_json['error']['type'])
                            except:
                                raise InvalidRequestError(f"OpenAI Invalid Request: HTTP {response.status_code}", code="invalid_request")
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
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                    elif e.response.status_code == 429:
                        raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                    elif e.response.status_code == 400:
                        raise InvalidRequestError(f"OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                    else:
                        raise APIConnectionError(f"OpenAI API error: {e.response.status_code}", code="api_error")
                except Exception as e:
                    raise APIConnectionError(f"OpenAI Connection error: {str(e)}", code="connection_error")
            
            return stream_generator()
        else:
            # Non-streaming
            try:
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
                    error_type = error.get('type', '')
                    message = error.get('message', 'Unknown error')
                    if error_type == 'invalid_request_error' or response.status_code == 400:
                        raise InvalidRequestError(message, param=error.get('param', ''), code=error_type)
                    elif error_type == 'authentication_error' or response.status_code == 401:
                        raise AuthenticationError(message, code="unauthorized")
                    elif error_type == 'rate_limit_error' or response.status_code == 429:
                        raise RateLimitError(message, code="rate_limit")
                    else:
                        raise APIConnectionError(message, code=error_type)
                
                # Handle usage
                if 'usage' in data:
                    data['usage'] = {
                        'prompt_tokens': data['usage']['prompt_tokens'],
                        'completion_tokens': data['usage']['completion_tokens'],
                        'total_tokens': data['usage']['total_tokens']
                    }
                
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"OpenAI API error: {e.response.status_code}", code="api_error")

    async def create_text_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create text completion using OpenAI API with streaming support"""
        self._validate_request(request, is_chat=False)
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                try:
                    async with self.make_request(
                        "POST",
                        f"{self.config.base_url}/completions",
                        json=request,
                        headers=headers,
                        stream=True
                    ) as response:
                        if response.status_code == 401:
                            raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                        elif response.status_code == 429:
                            raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                        elif response.status_code == 400:
                            error_data = await response.aread()
                            try:
                                error_json = json.loads(error_data)
                                raise InvalidRequestError(error_json['error']['message'], code=error_json['error']['type'])
                            except:
                                raise InvalidRequestError(f"OpenAI Invalid Request: HTTP {response.status_code}", code="invalid_request")
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
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                    elif e.response.status_code == 429:
                        raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                    elif e.response.status_code == 400:
                        raise InvalidRequestError(f"OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                    else:
                        raise APIConnectionError(f"OpenAI API error: {e.response.status_code}", code="api_error")
                except Exception as e:
                    raise APIConnectionError(f"OpenAI Connection error: {str(e)}", code="connection_error")
            
            return stream_generator()
        else:
            # Non-streaming
            try:
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
                    error_type = error.get('type', '')
                    message = error.get('message', 'Unknown error')
                    if error_type == 'invalid_request_error' or response.status_code == 400:
                        raise InvalidRequestError(message, param=error.get('param', ''), code=error_type)
                    elif error_type == 'authentication_error' or response.status_code == 401:
                        raise AuthenticationError(message, code="unauthorized")
                    elif error_type == 'rate_limit_error' or response.status_code == 429:
                        raise RateLimitError(message, code="rate_limit")
                    else:
                        raise APIConnectionError(message, code=error_type)
                
                # Handle usage
                if 'usage' in data:
                    data['usage'] = {
                        'prompt_tokens': data['usage']['prompt_tokens'],
                        'completion_tokens': data['usage']['completion_tokens'],
                        'total_tokens': data['usage']['total_tokens']
                    }
                
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"OpenAI API error: {e.response.status_code}", code="api_error")

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using OpenAI API"""
        self._validate_request(request, is_chat=False)  # Reuse for model and input
        if not request.get('input'):
            raise InvalidRequestError("Missing required 'input' parameter", param="input", code="missing_input")
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
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
                error_type = error.get('type', '')
                message = error.get('message', 'Unknown error')
                if error_type == 'invalid_request_error' or response.status_code == 400:
                    raise InvalidRequestError(message, param=error.get('param', ''), code=error_type)
                elif error_type == 'authentication_error' or response.status_code == 401:
                    raise AuthenticationError(message, code="unauthorized")
                elif error_type == 'rate_limit_error' or response.status_code == 429:
                    raise RateLimitError(message, code="rate_limit")
                else:
                    raise APIConnectionError(message, code=error_type)
            
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise AuthenticationError("OpenAI Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("OpenAI Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"OpenAI Invalid Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"OpenAI API error: {e.response.status_code}", code="api_error")
