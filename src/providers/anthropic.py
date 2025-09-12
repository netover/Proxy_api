from typing import Dict, Any, Union, AsyncGenerator, Set
from typing import Dict, Any, Union, AsyncGenerator
from src.core.provider_factory import BaseProvider, ProviderCapability
from src.core.unified_config import ProviderConfig
import json
import httpx
import time
from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError

class AnthropicProvider(BaseProvider):
    """Anthropic API provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    def _get_capabilities(self) -> Set[ProviderCapability]:
        """Get Anthropic provider capabilities"""
        from src.core.provider_factory import ProviderCapability
        capabilities = super()._get_capabilities()

        # Anthropic doesn't support embeddings
        capabilities.discard(ProviderCapability.EMBEDDINGS)

        return capabilities
        super().__init__(config)

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Health check for Anthropic API - use a simple messages request"""
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            response = await self.make_request(
                "POST", f"{self.config.base_url}/v1/messages",
                json={"model": "claude-3-opus-20240229", "max_tokens": 1, "messages": [{"role": "user", "content": "Hello"}]},
                headers=headers
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

    def _validate_request(self, request: Dict[str, Any]):
        """Validate required parameters for Anthropic requests"""
        if not request.get('model'):
            raise InvalidRequestError("Missing required 'model' parameter", param="model", code="missing_model")
        if not request.get('messages'):
            raise InvalidRequestError("Missing required 'messages' parameter", param="messages", code="missing_messages")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 1:
            raise InvalidRequestError("temperature must be a number between 0 and 1", param="temperature", code="invalid_value")

    def _transform_payload(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Transform OpenAI-style messages to Anthropic prompt format"""
        messages = request.get('messages', [])
        if not messages:
            raise InvalidRequestError("No messages provided", code="no_messages")
        
        prompt_parts = []
        for msg in messages:
            role = msg.get('role', '')
            content = msg.get('content', '')
            if role == 'user':
                prompt_parts.append(f"Human: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"Assistant: {content}")
            else:
                prompt_parts.append(f"{role.capitalize()}: {content}")
        
        prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
        
        anthropic_request = {
            "model": request.get('model'),
            "prompt": prompt,
            "max_tokens_to_sample": request.get('max_tokens', 1024),
            "temperature": request.get('temperature', 0.7),
            "stop_sequences": request.get('stop', ["Human:", "\n\nHuman:"]) + request.get('stop_sequences', []),
            "stream": request.get('stream', False)
        }
        if 'top_p' in request:
            anthropic_request['top_p'] = request['top_p']
        return anthropic_request

    def _parse_response(self, anthropic_response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Anthropic response to OpenAI-compatible format"""
        content = anthropic_response.get('content', [{}])[0].get('text', '')
        stop_reason = anthropic_response.get('stop_reason', 'stop')
        finish_reason = {
            'end_turn': 'stop',
            'max_tokens': 'length',
            'stop_sequence': 'stop',
        }.get(stop_reason, 'stop')
        
        return {
            "id": anthropic_response.get('id', ''),
            "object": "chat.completion",
            "created": int(anthropic_response.get('created', time.time())),
            "model": anthropic_response.get('model', ''),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": finish_reason
            }],
            "usage": anthropic_response.get('usage', {})
        }

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion using Anthropic API with streaming support"""
        self._validate_request(request)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        anthropic_request = self._transform_payload(request)
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                try:
                    async with self.make_request(
                        "POST",
                        f"{self.config.base_url}/v1/messages",
                        json=anthropic_request,
                        headers=headers,
                        stream=True
                    ) as response:
                        if response.status_code == 401:
                            raise AuthenticationError("Anthropic Authentication failed", code="unauthorized")
                        elif response.status_code == 429:
                            raise RateLimitError("Anthropic Rate limit exceeded", code="rate_limit")
                        elif response.status_code == 400:
                            error_data = await response.aread()
                            try:
                                error_json = json.loads(error_data)
                                raise InvalidRequestError(error_json.get('error', {}).get('message', 'Invalid request'), code="invalid_request")
                            except (json.JSONDecodeError, KeyError):
                                raise InvalidRequestError(f"Anthropic Invalid Request: HTTP {response.status_code}", code="invalid_request")
                        response.raise_for_status()
                        
                        async for line in response.aiter_lines():
                            if line.startswith('data: '):
                                data = line[6:]
                                if data == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(data)
                                    # Parse chunk to OpenAI format
                                    parsed_chunk = {
                                        "id": chunk.get('id', ''),
                                        "object": "chat.completion.chunk",
                                        "created": int(chunk.get('created', time.time())),
                                        "model": chunk.get('model', ''),
                                        "choices": [{
                                            "index": 0,
                                            "delta": {
                                                "role": "assistant",
                                                "content": chunk.get('content', [{}])[0].get('text_delta', '')
                                            },
                                            "finish_reason": None
                                        }]
                                    }
                                    if 'stop_reason' in chunk and chunk['stop_reason']:
                                        parsed_chunk['choices'][0]['finish_reason'] = {
                                            'end_turn': 'stop',
                                            'max_tokens': 'length',
                                            'stop_sequence': 'stop',
                                        }.get(chunk['stop_reason'], 'stop')
                                    yield f"data: {json.dumps(parsed_chunk)}\n\n"
                                except json.JSONDecodeError:
                                    continue
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        raise AuthenticationError("Anthropic Authentication failed", code="unauthorized")
                    elif e.response.status_code == 429:
                        raise RateLimitError("Anthropic Rate limit exceeded", code="rate_limit")
                    elif e.response.status_code == 400:
                        raise InvalidRequestError(f"Anthropic Invalid Request: {e.response.text}", code="invalid_request")
                    else:
                        raise APIConnectionError(f"Anthropic API error: {e.response.status_code}", code="api_error")
                except Exception as e:
                    raise APIConnectionError(f"Anthropic Connection error: {str(e)}", code="connection_error")
            
            return stream_generator()
        else:
            # Non-streaming
            try:
                response = await self.make_request(
                    "POST",
                    f"{self.config.base_url}/v1/messages",
                    json=anthropic_request,
                    headers=headers
                )
                data = response.json()
                
                # Specific error handling
                if 'error' in data:
                    error = data['error']
                    message = error.get('message', 'Unknown error')
                    error_type = error.get('type', '')
                    if error_type == 'invalid_request' or response.status_code == 400:
                        raise InvalidRequestError(message, code=error_type)
                    elif response.status_code == 401:
                        raise AuthenticationError(message, code="unauthorized")
                    elif response.status_code == 429:
                        raise RateLimitError(message, code="rate_limit")
                    else:
                        raise APIConnectionError(message, code=error_type)
                
                # Parse to OpenAI format
                return self._parse_response(data)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AuthenticationError("Anthropic Authentication failed", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("Anthropic Rate limit exceeded", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"Anthropic Invalid Request: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"Anthropic API error: {e.response.status_code}", code="api_error")

    async def create_text_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create text completion using Anthropic API (transformed to messages)"""
        self._validate_request(request)
        # Transform prompt to messages
        request['messages'] = [{"role": "user", "content": request.get("prompt", "")}]
        return await self.create_completion(request)

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Anthropic does not support embeddings"""
        raise NotImplementedError("Anthropic API does not support embeddings")
