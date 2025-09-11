"""
Azure OpenAI provider implementation
Uses deployment endpoint with api-key auth and OpenAI-compatible payload
Supports api_version query param
"""

from typing import Dict, Any, Union, AsyncGenerator
import json
import time
import httpx
from urllib.parse import urlencode
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
from src.core.metrics import metrics_collector
from src.core.logging import ContextualLogger
from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI provider with deployment-based endpoint"""

    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or f"https://{config.get('resource', 'your-resource')}.openai.azure.com"
        self.deployment_id = config.get('deployment_id', 'your-deployment')
        self.api_version = config.get('api_version', '2023-12-01-preview')
        self.logger = ContextualLogger(f"provider.{config.name}")

    async def _perform_health_check(self) -> Dict[str, Any]:
        """Health check for Azure OpenAI using deployments list"""
        try:
            params = {'api-version': self.api_version}
            headers = {"api-key": self.api_key}
            response = await self.make_request(
                "GET",
                f"{self.base_url}/openai/deployments?{urlencode(params)}",
                headers=headers
            )
            return {
                "healthy": response.status_code == 200,
                "details": {"status_code": response.status_code}
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {"healthy": False, "error": str(e)}

    def _validate_request(self, request: Dict[str, Any]):
        """Validate required parameters for Azure OpenAI requests"""
        if not request.get('model'):
            raise InvalidRequestError("Missing required 'model' parameter (deployment name)", param="model", code="missing_model")
        if not request.get('messages') and not request.get('prompt'):
            raise InvalidRequestError("Missing required 'messages' or 'prompt' parameter", code="missing_input")
        if 'max_tokens' in request and not isinstance(request['max_tokens'], int):
            raise InvalidRequestError("max_tokens must be an integer", param="max_tokens", code="invalid_type")
        if 'temperature' in request and not isinstance(request['temperature'], (int, float)) or request['temperature'] < 0 or request['temperature'] > 2:
            raise InvalidRequestError("temperature must be a number between 0 and 2", param="temperature", code="invalid_value")

    async def create_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create chat completion using Azure OpenAI (supports streaming)"""
        self._validate_request(request)
        start_time = time.time()
        params = {'api-version': self.api_version}
        endpoint = f"{self.base_url}/openai/deployments/{self.deployment_id}/chat/completions"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        
        if request.get('stream', False):
            # Streaming response
            async def stream_generator():
                try:
                    async with self.make_request(
                        "POST",
                        f"{endpoint}?{urlencode(params)}",
                        json=request,
                        headers=headers,
                        stream=True
                    ) as response:
                        if response.status_code == 401:
                            raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                        elif response.status_code == 429:
                            raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                        elif response.status_code == 400:
                            error_data = await response.aread()
                            try:
                                error_json = json.loads(error_data)
                                raise InvalidRequestError(error_json['error']['message'], code=error_json['error']['type'])
                            except (json.JSONDecodeError, KeyError):
                                raise InvalidRequestError(f"Azure OpenAI Invalid Request: HTTP {response.status_code}", code="invalid_request")
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
                        raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                    elif e.response.status_code == 429:
                        raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                    elif e.response.status_code == 400:
                        raise InvalidRequestError(f"Azure OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                    else:
                        raise APIConnectionError(f"Azure OpenAI API error: {e.response.status_code}", code="api_error")
                except Exception as e:
                    raise APIConnectionError(f"Azure OpenAI Connection error: {str(e)}", code="connection_error")
            
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=0  # Tokens not available in streaming
            )
            self.logger.info("Azure OpenAI chat completion streaming successful", response_time=response_time)
            return stream_generator()
        else:
            # Non-streaming
            try:
                response = await self.make_request(
                    "POST",
                    f"{endpoint}?{urlencode(params)}",
                    json=request,
                    headers=headers
                )
                data = response.json()
                
                # Specific error handling
                if 'error' in data:
                    error = data['error']
                    error_type = error.get('type', '')
                    message = error.get('message', 'Unknown error')
                    if error_type == 'invalid_request' or response.status_code == 400:
                        raise InvalidRequestError(message, code=error_type)
                    elif response.status_code == 401:
                        raise AuthenticationError(message, code="unauthorized")
                    elif response.status_code == 429:
                        raise RateLimitError(message, code="rate_limit")
                    else:
                        raise APIConnectionError(message, code=error_type)
                
                response_time = time.time() - start_time
                
                # Record metrics
                usage = data.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)
                metrics_collector.record_request(
                    self.name,
                    success=True,
                    response_time=response_time,
                    tokens=total_tokens
                )
                self.logger.info("Azure OpenAI chat completion successful", response_time=response_time, tokens=total_tokens)
                
                return data
            except httpx.HTTPStatusError as e:
                response_time = time.time() - start_time
                metrics_collector.record_request(
                    self.name,
                    success=False,
                    response_time=response_time,
                    error_type=type(e).__name__
                )
                if e.response.status_code == 401:
                    raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"Azure OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"Azure OpenAI API error: {e.response.status_code}", code="api_error")

    async def create_text_completion(self, request: Dict[str, Any]) -> Union[Dict[str, Any], AsyncGenerator]:
        """Create text completion using Azure OpenAI completions endpoint"""
        self._validate_request(request)
        start_time = time.time()
        params = {'api-version': self.api_version}
        endpoint = f"{self.base_url}/openai/deployments/{self.deployment_id}/completions"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        
        if request.get('stream', False):
            # Streaming for text completion
            async def stream_generator():
                try:
                    async with self.make_request(
                        "POST",
                        f"{endpoint}?{urlencode(params)}",
                        json=request,
                        headers=headers,
                        stream=True
                    ) as response:
                        if response.status_code == 401:
                            raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                        elif response.status_code == 429:
                            raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                        elif response.status_code == 400:
                            error_data = await response.aread()
                            try:
                                error_json = json.loads(error_data)
                                raise InvalidRequestError(error_json['error']['message'], code=error_json['error']['type'])
                            except (json.JSONDecodeError, KeyError):
                                raise InvalidRequestError(f"Azure OpenAI Invalid Request: HTTP {response.status_code}", code="invalid_request")
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
                        raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                    elif e.response.status_code == 429:
                        raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                    elif e.response.status_code == 400:
                        raise InvalidRequestError(f"Azure OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                    else:
                        raise APIConnectionError(f"Azure OpenAI API error: {e.response.status_code}", code="api_error")
                except Exception as e:
                    raise APIConnectionError(f"Azure OpenAI Connection error: {str(e)}", code="connection_error")
            
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=0  # Tokens not available in streaming
            )
            self.logger.info("Azure OpenAI text completion streaming successful", response_time=response_time)
            return stream_generator()
        else:
            # Non-streaming
            try:
                response = await self.make_request(
                    "POST",
                    f"{endpoint}?{urlencode(params)}",
                    json=request,
                    headers=headers
                )
                data = response.json()
                
                # Specific error handling
                if 'error' in data:
                    error = data['error']
                    error_type = error.get('type', '')
                    message = error.get('message', 'Unknown error')
                    if error_type == 'invalid_request' or response.status_code == 400:
                        raise InvalidRequestError(message, code=error_type)
                    elif response.status_code == 401:
                        raise AuthenticationError(message, code="unauthorized")
                    elif response.status_code == 429:
                        raise RateLimitError(message, code="rate_limit")
                    else:
                        raise APIConnectionError(message, code=error_type)
                
                response_time = time.time() - start_time
                
                # Record metrics
                usage = data.get("usage", {})
                total_tokens = usage.get("total_tokens", 0)
                metrics_collector.record_request(
                    self.name,
                    success=True,
                    response_time=response_time,
                    tokens=total_tokens
                )
                self.logger.info("Azure OpenAI text completion successful", response_time=response_time, tokens=total_tokens)
                
                return data
            except httpx.HTTPStatusError as e:
                response_time = time.time() - start_time
                metrics_collector.record_request(
                    self.name,
                    success=False,
                    response_time=response_time,
                    error_type=type(e).__name__
                )
                if e.response.status_code == 401:
                    raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
                elif e.response.status_code == 429:
                    raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
                elif e.response.status_code == 400:
                    raise InvalidRequestError(f"Azure OpenAI Invalid Request: {e.response.text}", code="invalid_request")
                else:
                    raise APIConnectionError(f"Azure OpenAI API error: {e.response.status_code}", code="api_error")

    async def create_embeddings(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create embeddings using Azure OpenAI embeddings endpoint"""
        self._validate_request(request)
        if not request.get('input'):
            raise InvalidRequestError("Missing required 'input' parameter for embeddings", param="input", code="missing_input")
        start_time = time.time()
        params = {'api-version': self.api_version}
        endpoint = f"{self.base_url}/openai/deployments/{self.deployment_id}/embeddings"
        headers = {"api-key": self.api_key, "Content-Type": "application/json"}
        try:
            response = await self.make_request(
                "POST",
                f"{endpoint}?{urlencode(params)}",
                json=request,
                headers=headers
            )
            data = response.json()
            
            # Specific error handling
            if 'error' in data:
                error = data['error']
                error_type = error.get('type', '')
                message = error.get('message', 'Unknown error')
                if error_type == 'invalid_request' or response.status_code == 400:
                    raise InvalidRequestError(message, code=error_type)
                elif response.status_code == 401:
                    raise AuthenticationError(message, code="unauthorized")
                elif response.status_code == 429:
                    raise RateLimitError(message, code="rate_limit")
                else:
                    raise APIConnectionError(message, code=error_type)
            
            response_time = time.time() - start_time
            
            # Record metrics
            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            metrics_collector.record_request(
                self.name,
                success=True,
                response_time=response_time,
                tokens=total_tokens
            )
            self.logger.info("Azure OpenAI embeddings successful", response_time=response_time, tokens=total_tokens)
            
            return data
        except httpx.HTTPStatusError as e:
            response_time = time.time() - start_time
            metrics_collector.record_request(
                self.name,
                success=False,
                response_time=response_time,
                error_type=type(e).__name__
            )
            if e.response.status_code == 401:
                raise AuthenticationError("Azure OpenAI Authentication failed", code="unauthorized")
            elif e.response.status_code == 429:
                raise RateLimitError("Azure OpenAI Rate limit exceeded", code="rate_limit")
            elif e.response.status_code == 400:
                raise InvalidRequestError(f"Azure OpenAI Invalid Request: {e.response.text}", code="invalid_request")
            else:
                raise APIConnectionError(f"Azure OpenAI API error: {e.response.status_code}", code="api_error")