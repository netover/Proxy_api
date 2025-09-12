"""Base discovery provider for model discovery capabilities."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.exceptions import ProviderError, ValidationError
from ..models.model_info import ModelInfo

logger = logging.getLogger(__name__)


class BaseDiscoveryProvider(ABC):
    """
    Abstract base class for providers that support model discovery.
    
    This class defines the interface for providers that can discover and
    retrieve model information from their respective APIs. It provides
    a standardized way to interact with different providers' model
    discovery capabilities while maintaining backward compatibility.
    
    The discovery methods should:
    - Return standardized ModelInfo objects
    - Handle provider-specific API differences
    - Implement proper error handling
    - Support caching integration
    - Maintain backward compatibility with existing providers
    
    Example:
        class MyProvider(BaseDiscoveryProvider):
            async def list_models(self) -> List[ModelInfo]:
                # Implementation specific to this provider
                pass
                
            async def retrieve_model(self, model_id: str) -> Optional[ModelInfo]:
                # Implementation specific to this provider
                pass
    """
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """
        Discover all available models from this provider.
        
        This method should query the provider's API to retrieve a complete
        list of available models and return them as standardized ModelInfo
        objects.
        
        Returns:
            List of ModelInfo objects representing all available models
            
        Raises:
            ProviderError: If the provider is unreachable or returns an error
            ValidationError: If the response format is invalid
            
        Example:
            >>> models = await provider.list_models()
            >>> print(f"Found {len(models)} models")
            >>> for model in models:
            ...     print(f"{model.id} by {model.owned_by}")
        """
    
    @abstractmethod
    async def retrieve_model(self, model_id: str) -> Optional[ModelInfo]:
        """
        Retrieve detailed information for a specific model.
        
        This method should query the provider's API to retrieve detailed
        information about a specific model by its ID.
        
        Args:
            model_id: The unique identifier of the model to retrieve
            
        Returns:
            ModelInfo object if the model exists, None otherwise
            
        Raises:
            ProviderError: If the provider is unreachable or returns an error
            ValidationError: If the response format is invalid
            
        Example:
            >>> model_info = await provider.retrieve_model("gpt-4")
            >>> if model_info:
            ...     print(f"Model created: {model_info.created_datetime}")
            ... else:
            ...     print("Model not found")
        """
    
    async def validate_model(self, model_id: str) -> bool:
        """
        Validate if a specific model exists and is accessible.
        
        This is a convenience method that uses retrieve_model to check
        if a model exists without returning the full model information.
        
        Args:
            model_id: The model ID to validate
            
        Returns:
            True if the model exists and is accessible, False otherwise
            
        Example:
            >>> if await provider.validate_model("gpt-4"):
            ...     print("Model is available")
            ... else:
            ...     print("Model not found or inaccessible")
        """
        try:
            model_info = await self.retrieve_model(model_id)
            return model_info is not None
        except (ProviderError, ValidationError):
            return False
    
    async def get_models_by_owner(self, owner: str) -> List[ModelInfo]:
        """
        Get all models owned by a specific organization.
        
        Args:
            owner: The organization name to filter by
            
        Returns:
            List of ModelInfo objects owned by the specified organization
            
        Example:
            >>> openai_models = await provider.get_models_by_owner("openai")
            >>> print(f"OpenAI has {len(openai_models)} models available")
        """
        try:
            all_models = await self.list_models()
            return [model for model in all_models if model.owned_by == owner]
        except (ProviderError, ValidationError):
            return []
    
    async def get_models_created_after(self, timestamp: int) -> List[ModelInfo]:
        """
        Get all models created after a specific timestamp.
        
        Args:
            timestamp: Unix timestamp to filter by
            
        Returns:
            List of ModelInfo objects created after the specified timestamp
            
        Example:
            >>> import time
            >>> recent_models = await provider.get_models_created_after(
            ...     int(time.time()) - 86400  # Last 24 hours
            ... )
        """
        try:
            all_models = await self.list_models()
            return [model for model in all_models if model.created > timestamp]
        except (ProviderError, ValidationError):
            return []
    
    async def search_models(self, query: str) -> List[ModelInfo]:
        """
        Search for models by ID or other attributes.
        
        This method provides a simple search capability across model IDs.
        More sophisticated search can be implemented by providers as needed.
        
        Args:
            query: Search query to match against model IDs
            
        Returns:
            List of ModelInfo objects matching the search query
            
        Example:
            >>> gpt_models = await provider.search_models("gpt")
            >>> print(f"Found {len(gpt_models)} GPT models")
        """
        try:
            all_models = await self.list_models()
            query_lower = query.lower()
            return [
                model for model in all_models
                if query_lower in model.id.lower()
            ]
        except (ProviderError, ValidationError):
            return []