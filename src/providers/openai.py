from typing import Dict, Any, Union, AsyncGenerator, List, Optional, Set
from typing import Dict, Any, Union, AsyncGenerator, List, Optional
from src.core.provider_factory import BaseProvider
from src.core.unified_config import ProviderConfig
from src.models.model_info import ModelInfo
from src.core.consolidated_cache import get_consolidated_cache_manager
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig as DiscoveryProviderConfig
from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
import json
import httpx
from src.core.provider_factory import BaseProvider, ProviderCapability
import time

from src.core.exceptions import InvalidRequestError, AuthenticationError, RateLimitError, APIConnectionError

class OpenAIProvider(BaseProvider):
    """OpenAI API provider implementation with model discovery support"""
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._discovery_service = None
        self._cache_manager = None
        self.logger = ContextualLogger(f"provider.{config.name}")

    def _get_capabilities(self) -> Set[ProviderCapability]:
        """Get OpenAI provider capabilities"""
        from src.core.provider_factory import ProviderCapability
        capabilities = super()._get_capabilities()

        # OpenAI supports model discovery
        capabilities.add(ProviderCapability.MODEL_DISCOVERY)

        return capabilities
        self.logger = ContextualLogger(f"provider.{config.name}")
    
    @property
    def discovery_service(self):
        """Lazy-loaded model discovery service"""
        if self._discovery_service is None:
            self._discovery_service = ModelDiscoveryService()
        return self._discovery_service
    
    @property
    def model_cache(self):
        """Lazy-loaded model cache"""
        if self._cache_manager is None:
            self._model_cache = ModelCache(
                ttl=300,  # 5 minutes default
                max_size=1000,
                persist=True
            )
        return self._model_cache

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
        start_time = time.time()
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
                            except (json.JSONDecodeError, KeyError):
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

                # Record metrics and log success
                usage = data.get('usage', {})
                total_tokens = usage.get('total_tokens', 0)
                response_time = time.time() - start_time
                metrics_collector.record_request(
                    self.name,
                    success=True,
                    response_time=response_time,
                    tokens=total_tokens
                )
                self.logger.info("Chat completion successful",
                               model=request.get('model'),
                               response_time=response_time,
                               tokens=total_tokens)

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
    
    async def list_models(self) -> List[ModelInfo]:
        """
        Discover all available models from OpenAI.
        
        This method queries the OpenAI /v1/models endpoint and returns
        a list of ModelInfo objects for all available models.
        
        Returns:
            List of ModelInfo objects for all available models
            
        Raises:
            ProviderError: If the provider is unreachable or returns an error
            ValidationError: If the response format is invalid
        """
        # Check cache first
        cached_models = self.model_cache.get_models(self.name, self.config.base_url)
        if cached_models is not None:
            return cached_models
        
        # Create discovery provider config
        discovery_config = DiscoveryProviderConfig(
            name=self.name,
            base_url=self.config.base_url,
            api_key=self.api_key,
            organization=getattr(self.config, 'organization', None),
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )
        
        try:
            # Discover models using the discovery service
            models = await self.discovery_service.discover_models(discovery_config)
            
            # Cache the results
            self.model_cache.set_models(self.name, self.config.base_url, models)
            
            return models
            
        except Exception as e:
            raise APIConnectionError(f"Failed to discover models: {str(e)}", code="discovery_error")
    
    async def retrieve_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Retrieve detailed information for a specific OpenAI model.
        
        Args:
            model_id: The model ID to retrieve (e.g., "gpt-4", "gpt-3.5-turbo")
            
        Returns:
            ModelInfo object if the model exists, None otherwise
            
        Raises:
            ProviderError: If the provider is unreachable or returns an error
            ValidationError: If the response format is invalid
        """
        # First, try to get from the full model list
        try:
            all_models = await self.list_models()
            for model in all_models:
                if model.id == model_id:
                    return model
            return None
            
        except Exception as e:
            # Fallback to direct model retrieval if list fails
            try:
                response = await self.make_request(
                    "GET",
                    f"{self.config.base_url}/models/{model_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code == 404:
                    return None
                
                data = response.json()
                return ModelInfo.from_dict(data)
                
            except Exception as fallback_error:
                raise APIConnectionError(
                    f"Failed to retrieve model {model_id}: {str(fallback_error)}",
                    code="model_retrieval_error"
                )
    
    async def close(self) -> None:
        """Close the provider and cleanup resources"""
        await super().close()
        
        # Close discovery service
        if self._discovery_service:
            await self._discovery_service.close()
            self._discovery_service = None
        
        # Close model cache
        if self._model_cache:
            self._model_cache.close()
            self._cache_manager = None

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
                            except (json.JSONDecodeError, KeyError):
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
