"""
RESTful API endpoints for model management.

This module provides endpoints for managing models across different providers,
including listing, retrieving details, updating selections, and cache management.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import time
import logging

from src.core.auth import verify_api_key
from src.core.rate_limiter import rate_limiter
from src.core.exceptions import InvalidRequestError, NotFoundError
from src.models.requests import (
    ModelSelectionRequest,
    ModelListResponse,
    ModelDetailResponse,
    RefreshResponse,
    ModelInfoExtended
)
from src.core.provider_factory import ProviderStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/providers", tags=["model-management"])

class ModelManager:
    """Centralized model management with caching and provider integration."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def get_provider_models(self, request: Request, provider_name: str) -> ModelListResponse:
        """Get all models for a specific provider."""
        app_state = request.app.state.app_state
        
        # Validate provider exists
        provider_info = await app_state.provider_factory.get_all_provider_info()
        provider = next((p for p in provider_info if p.name.lower() == provider_name.lower()), None)
        
        if not provider:
            raise NotFoundError(f"Provider '{provider_name}' not found")
        
        # Get models from cache or discovery
        try:
            # Create provider config for discovery
            from src.core.model_discovery import ProviderConfig
            provider_config = ProviderConfig(
                name=provider.name,
                base_url=provider.base_url,
                api_key=provider.api_key or "dummy-key"
            )
            models = await app_state.model_discovery.discover_models(provider_config)
            
            # Convert to extended model format
            extended_models = []
            for model in models:
                extended_model = ModelInfoExtended(
                    id=model.id,
                    created=model.created,
                    owned_by=model.owned_by,
                    provider=provider_name,
                    status="active",
                    capabilities=self._infer_capabilities(model.id),
                    description=f"Model {model.id} from {provider_name}"
                )
                extended_models.append(extended_model)
            
            return ModelListResponse(
                object="list",
                data=extended_models,
                provider=provider_name,
                total=len(extended_models),
                cached=True,  # TODO: Check if from cache
                last_refresh=int(time.time())
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get models for provider {provider_name}: {e}")
            raise InvalidRequestError(f"Failed to retrieve models: {str(e)}")
    
    async def get_model_details(self, request: Request, provider_name: str, model_id: str) -> ModelDetailResponse:
        """Get detailed information for a specific model."""
        app_state = request.app.state.app_state
        
        # Validate provider exists
        provider_info = await app_state.provider_factory.get_all_provider_info()
        provider = next((p for p in provider_info if p.name.lower() == provider_name.lower()), None)
        
        if not provider:
            raise NotFoundError(f"Provider '{provider_name}' not found")
        
        # Get model details
        try:
            from src.core.model_discovery import ProviderConfig
            provider_config = ProviderConfig(
                name=provider.name,
                base_url=provider.base_url,
                api_key=provider.api_key or "dummy-key"
            )
            model = await app_state.model_discovery.get_model_info(provider_config, model_id)
            
            if not model:
                raise NotFoundError(f"Model '{model_id}' not found for provider '{provider_name}'")
            
            extended_model = ModelInfoExtended(
                id=model.id,
                created=model.created,
                owned_by=model.owned_by,
                provider=provider_name,
                status="active",
                capabilities=self._infer_capabilities(model.id),
                description=f"Model {model.id} from {provider_name}",
                last_updated=int(time.time())
            )
            
            return ModelDetailResponse(
                object="model",
                data=extended_model,
                provider=provider_name,
                cached=True,
                last_refresh=int(time.time())
            )
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get model details for {provider_name}/{model_id}: {e}")
            raise InvalidRequestError(f"Failed to retrieve model details: {str(e)}")
    
    async def update_model_selection(self, request: Request, provider_name: str, selection: ModelSelectionRequest) -> Dict[str, Any]:
        """Update model selection configuration for a provider."""
        app_state = request.app.state.app_state
        
        # Validate provider exists
        provider_info = await app_state.provider_factory.get_all_provider_info()
        provider = next((p for p in provider_info if p.name.lower() == provider_name.lower()), None)
        
        if not provider:
            raise NotFoundError(f"Provider '{provider_name}' not found")
        
        # Validate model exists for provider
        from src.core.model_discovery import ProviderConfig
        provider_config = ProviderConfig(
            name=provider.name,
            base_url=provider.base_url,
            api_key=provider.api_key or "dummy-key"
        )
        model = await app_state.model_discovery.get_model_info(
            provider_config, selection.selected_model
        )
        
        if not model:
            raise NotFoundError(
                f"Model '{selection.selected_model}' not found for provider '{provider_name}'"
            )
        
        # Update configuration
        try:
            config = app_state.config_manager.load_config()
            
            # Update provider-specific model selection
            provider_config = config.providers.get(provider_name, {})
            provider_config.update({
                "selected_model": selection.selected_model,
                "editable": selection.editable,
                "priority": selection.priority,
                "max_tokens": selection.max_tokens,
                "temperature": selection.temperature
            })
            config.providers[provider_name] = provider_config
            
            # Save configuration
            app_state.config_manager.save_config(config)
            
            logger.info(
                f"Updated model selection for provider {provider_name}",
                selected_model=selection.selected_model,
                editable=selection.editable,
                priority=selection.priority
            )
            
            return {
                "success": True,
                "provider": provider_name,
                "selected_model": selection.selected_model,
                "updated_at": int(time.time()),
                "message": f"Model selection updated for provider '{provider_name}'"
            }
            
        except Exception as e:
            logger.error(f"Failed to update model selection for {provider_name}: {e}")
            raise InvalidRequestError(f"Failed to update model selection: {str(e)}")
    
    async def refresh_models(self, request: Request, provider_name: str, background_tasks: BackgroundTasks) -> RefreshResponse:
        """Force refresh model cache for a provider."""
        app_state = request.app.state.app_state
        
        # Validate provider exists
        provider_info = await app_state.provider_factory.get_all_provider_info()
        provider = next((p for p in provider_info if p.name.lower() == provider_name.lower()), None)
        
        if not provider:
            raise NotFoundError(f"Provider '{provider_name}' not found")
        
        start_time = time.time()
        
        try:
            # Clear cache
            cache_cleared = await app_state.cache_manager.clear_provider_cache(provider_name)
            
            # Force refresh models
            from src.core.model_discovery import ProviderConfig
            provider_config = ProviderConfig(
                name=provider.name,
                base_url=provider.base_url,
                api_key=provider.api_key or "dummy-key"
            )
            models = await app_state.model_discovery.discover_models(provider_config)
            
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Refreshed models for provider {provider_name}",
                models_count=len(models),
                duration_ms=duration_ms,
                cache_cleared=cache_cleared
            )
            
            return RefreshResponse(
                success=True,
                provider=provider_name,
                models_refreshed=len(models),
                cache_cleared=cache_cleared,
                duration_ms=duration_ms,
                timestamp=int(time.time())
            )
            
        except Exception as e:
            logger.error(f"Failed to refresh models for {provider_name}: {e}")
            raise InvalidRequestError(f"Failed to refresh models: {str(e)}")
    
    def _infer_capabilities(self, model_id: str) -> List[str]:
        """Infer model capabilities based on model ID patterns."""
        capabilities = []
        model_lower = model_id.lower()
        
        # Text capabilities
        if any(x in model_lower for x in ["gpt", "claude", "llama", "gemini"]):
            capabilities.extend(["text_generation", "chat", "completion"])
        
        # Vision capabilities
        if any(x in model_lower for x in ["vision", "gpt-4-turbo", "claude-3", "gemini-pro-vision"]):
            capabilities.append("vision")
        
        # Embedding capabilities
        if "embedding" in model_lower or "text-embedding" in model_lower:
            capabilities.append("embeddings")
        
        # Image generation
        if "dall-e" in model_lower or "imagen" in model_lower:
            capabilities.append("image_generation")
        
        # Audio capabilities
        if "whisper" in model_lower or "audio" in model_lower:
            capabilities.extend(["audio_transcription", "audio_generation"])
        
        # Default capabilities
        if not capabilities:
            capabilities = ["text_generation"]
        
        return capabilities

# Initialize model manager
model_manager = ModelManager()

# RESTful endpoints

@router.get("/{provider_name}/models", response_model=ModelListResponse)
@rate_limiter.limit("60/minute")
async def list_provider_models(
    request: Request,
    provider_name: str,
    _: bool = Depends(verify_api_key)
):
    """
    List all models for a specific provider.
    
    - **provider_name**: Name of the provider (e.g., 'openai', 'anthropic')
    
    Returns a paginated list of models with extended information including
    capabilities, pricing, and metadata.
    """
    return await model_manager.get_provider_models(request, provider_name)

@router.get("/{provider_name}/models/{model_id}", response_model=ModelDetailResponse)
@rate_limiter.limit("60/minute")
async def get_model_info(
    request: Request,
    provider_name: str,
    model_id: str,
    _: bool = Depends(verify_api_key)
):
    """
    Get detailed information for a specific model.
    
    - **provider_name**: Name of the provider
    - **model_id**: Unique identifier of the model
    
    Returns comprehensive model information including capabilities,
    limitations, and configuration options.
    """
    return await model_manager.get_model_details(request, provider_name, model_id)

@router.put("/{provider_name}/model_selection", response_model=Dict[str, Any])
@rate_limiter.limit("30/minute")
async def update_model_selection(
    request: Request,
    provider_name: str,
    selection: ModelSelectionRequest,
    _: bool = Depends(verify_api_key)
):
    """
    Update model selection configuration for a provider.
    
    - **provider_name**: Name of the provider
    - **selection**: Model selection configuration
    
    Allows updating the default model selection, priority, and
    provider-specific configuration parameters.
    """
    return await model_manager.update_model_selection(request, provider_name, selection)

@router.post("/{provider_name}/models/refresh", response_model=RefreshResponse)
@rate_limiter.limit("10/minute")
async def refresh_provider_models(
    request: Request,
    provider_name: str,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """
    Force refresh model cache for a provider.
    
    - **provider_name**: Name of the provider
    
    Clears the model cache and performs a fresh discovery of available
    models from the provider's API. Useful when new models are released
    or existing models are updated.
    """
    return await model_manager.refresh_models(request, provider_name, background_tasks)

# Error handlers

@router.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """Handle not found errors with proper HTTP status."""
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": str(exc),
                "type": "not_found",
                "code": "resource_not_found"
            }
        }
    )

@router.exception_handler(InvalidRequestError)
async def invalid_request_handler(request: Request, exc: InvalidRequestError):
    """Handle invalid request errors with proper HTTP status."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": str(exc),
                "type": "invalid_request",
                "code": getattr(exc, 'code', 'invalid_request_error')
            }
        }
    )