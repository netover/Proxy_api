from typing import Any, Dict, List, Optional

from ..core.exceptions import ConfigurationError, ValidationError
from ..core.model_config import model_config_manager
from ..core.unified_config import config_manager


class ModelConfigService:
    """Service layer for model configuration management with validation and error handling"""
    
    def __init__(self):
        self._config_manager = config_manager
        self._model_manager = model_config_manager
    
    def get_model_selection(self, provider_name: str) -> Optional[str]:
        """
        Get the selected model for a specific provider
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Selected model name or None if no selection exists
            
        Raises:
            ValidationError: If provider doesn't exist
        """
        if not self._validate_provider_exists(provider_name):
            raise ValidationError(f"Provider '{provider_name}' not found")
        
        return self._config_manager.get_model_selection(provider_name)
    
    def set_model_selection(self, provider_name: str, model_name: str, editable: bool = True) -> Dict[str, Any]:
        """
        Set the model selection for a provider
        
        Args:
            provider_name: Name of the provider
            model_name: Name of the model to select
            editable: Whether this selection can be modified later
            
        Returns:
            Dictionary with success status and details
            
        Raises:
            ValidationError: If provider or model is invalid
            ConfigurationError: If configuration cannot be saved
        """
        # Validate provider exists
        if not self._validate_provider_exists(provider_name):
            raise ValidationError(f"Provider '{provider_name}' not found")
        
        # Validate model is supported by provider
        if not self._validate_model_supported(provider_name, model_name):
            available_models = self._config_manager.get_available_models(provider_name)
            raise ValidationError(
                f"Model '{model_name}' not supported by provider '{provider_name}'. "
                f"Available models: {available_models}"
            )
        
        try:
            self._config_manager.set_model_selection(provider_name, model_name, editable)
            return {
                "success": True,
                "provider": provider_name,
                "model": model_name,
                "editable": editable,
                "message": f"Model '{model_name}' selected for provider '{provider_name}'"
            }
        except Exception as e:
            raise ConfigurationError(f"Failed to save model selection: {str(e)}")
    
    def update_model_selection(self, provider_name: str, model_name: str) -> Dict[str, Any]:
        """
        Update an existing model selection if it's editable
        
        Args:
            provider_name: Name of the provider
            model_name: Name of the new model
            
        Returns:
            Dictionary with success status and details
            
        Raises:
            ValidationError: If provider, model, or selection is invalid
            ConfigurationError: If configuration cannot be saved
        """
        # Validate provider exists
        if not self._validate_provider_exists(provider_name):
            raise ValidationError(f"Provider '{provider_name}' not found")
        
        # Validate model is supported by provider
        if not self._validate_model_supported(provider_name, model_name):
            available_models = self._config_manager.get_available_models(provider_name)
            raise ValidationError(
                f"Model '{model_name}' not supported by provider '{provider_name}'. "
                f"Available models: {available_models}"
            )
        
        # Check if selection exists and is editable
        current_selection = self._model_manager.get_model_selection(provider_name)
        if not current_selection:
            raise ValidationError(f"No model selection exists for provider '{provider_name}'")
        
        if not current_selection.editable:
            raise ValidationError(
                f"Model selection for provider '{provider_name}' is not editable"
            )
        
        try:
            success = self._config_manager.update_model_selection(provider_name, model_name)
            if success:
                return {
                    "success": True,
                    "provider": provider_name,
                    "model": model_name,
                    "message": f"Model selection updated to '{model_name}' for provider '{provider_name}'"
                }
            else:
                raise ConfigurationError("Failed to update model selection")
        except Exception as e:
            raise ConfigurationError(f"Failed to update model selection: {str(e)}")
    
    def remove_model_selection(self, provider_name: str) -> Dict[str, Any]:
        """
        Remove the model selection for a provider
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary with success status and details
            
        Raises:
            ValidationError: If provider or selection is invalid
            ConfigurationError: If configuration cannot be saved
        """
        # Validate provider exists
        if not self._validate_provider_exists(provider_name):
            raise ValidationError(f"Provider '{provider_name}' not found")
        
        # Check if selection exists and is editable
        current_selection = self._model_manager.get_model_selection(provider_name)
        if not current_selection:
            return {
                "success": False,
                "message": f"No model selection exists for provider '{provider_name}'"
            }
        
        if not current_selection.editable:
            raise ValidationError(
                f"Model selection for provider '{provider_name}' is not editable"
            )
        
        try:
            success = self._config_manager.remove_model_selection(provider_name)
            if success:
                return {
                    "success": True,
                    "provider": provider_name,
                    "message": f"Model selection removed for provider '{provider_name}'"
                }
            else:
                raise ConfigurationError("Failed to remove model selection")
        except Exception as e:
            raise ConfigurationError(f"Failed to remove model selection: {str(e)}")
    
    def get_all_model_selections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all model selections with detailed information
        
        Returns:
            Dictionary mapping provider names to selection details
        """
        return self._config_manager.get_model_selection_details()
    
    def get_provider_model_info(self, provider_name: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a provider's model configuration
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary with provider model information
            
        Raises:
            ValidationError: If provider doesn't exist
        """
        if not self._validate_provider_exists(provider_name):
            raise ValidationError(f"Provider '{provider_name}' not found")
        
        selected_model = self.get_model_selection(provider_name)
        available_models = self._config_manager.get_available_models(provider_name)
        
        return {
            "provider": provider_name,
            "selected_model": selected_model,
            "available_models": available_models,
            "model_count": len(available_models),
            "has_selection": selected_model is not None,
            "selection_editable": self._is_selection_editable(provider_name)
        }
    
    def get_all_providers_model_info(self) -> List[Dict[str, Any]]:
        """
        Get model information for all providers
        
        Returns:
            List of provider model information dictionaries
        """
        providers = self._config_manager.load_config().providers
        return [
            self.get_provider_model_info(provider.name)
            for provider in providers
        ]
    
    def validate_model_selection(self, provider_name: str, model_name: str) -> Dict[str, Any]:
        """
        Validate if a model selection is valid
        
        Args:
            provider_name: Name of the provider
            model_name: Name of the model
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "valid": False,
            "provider_exists": False,
            "model_supported": False,
            "errors": []
        }
        
        # Check provider exists
        if not self._validate_provider_exists(provider_name):
            result["errors"].append(f"Provider '{provider_name}' not found")
            return result
        
        result["provider_exists"] = True
        
        # Check model is supported
        if not self._validate_model_supported(provider_name, model_name):
            available_models = self._config_manager.get_available_models(provider_name)
            result["errors"].append(
                f"Model '{model_name}' not supported. Available: {available_models}"
            )
            return result
        
        result["model_supported"] = True
        result["valid"] = True
        return result
    
    def bulk_set_model_selections(self, selections: Dict[str, str], editable: bool = True) -> Dict[str, Any]:
        """
        Set model selections for multiple providers
        
        Args:
            selections: Dictionary mapping provider names to model names
            editable: Whether these selections can be modified later
            
        Returns:
            Dictionary with bulk operation results
        """
        results = {
            "success": True,
            "total": len(selections),
            "successful": 0,
            "failed": 0,
            "errors": {},
            "results": {}
        }
        
        for provider_name, model_name in selections.items():
            try:
                result = self.set_model_selection(provider_name, model_name, editable)
                results["results"][provider_name] = result
                results["successful"] += 1
            except (ValidationError, ConfigurationError) as e:
                results["results"][provider_name] = {
                    "success": False,
                    "error": str(e)
                }
                results["errors"][provider_name] = str(e)
                results["failed"] += 1
        
        results["success"] = results["failed"] == 0
        return results
    
    def clear_all_model_selections(self, force: bool = False) -> Dict[str, Any]:
        """
        Clear all model selections
        
        Args:
            force: If True, clear all selections including non-editable ones
            
        Returns:
            Dictionary with operation results
        """
        try:
            count = self._model_manager.clear_all_selections(force=force)
            return {
                "success": True,
                "cleared_count": count,
                "message": f"Cleared {count} model selection(s)"
            }
        except Exception as e:
            raise ConfigurationError(f"Failed to clear model selections: {str(e)}")
    
    def reload_model_selections(self) -> Dict[str, Any]:
        """
        Force reload model selections from disk
        
        Returns:
            Dictionary with reload results
        """
        try:
            self._model_manager.reload()
            selections = self._model_manager.get_all_selections()
            return {
                "success": True,
                "loaded_count": len(selections),
                "selections": {k: v.model_name for k, v in selections.items()}
            }
        except Exception as e:
            raise ConfigurationError(f"Failed to reload model selections: {str(e)}")
    
    def _validate_provider_exists(self, provider_name: str) -> bool:
        """Check if a provider exists"""
        return self._config_manager.get_provider_by_name(provider_name) is not None
    
    def _validate_model_supported(self, provider_name: str, model_name: str) -> bool:
        """Check if a model is supported by a provider"""
        available_models = self._config_manager.get_available_models(provider_name)
        return model_name in available_models
    
    def _is_selection_editable(self, provider_name: str) -> bool:
        """Check if a model selection is editable"""
        selection = self._model_manager.get_model_selection(provider_name)
        return selection.editable if selection else True

# Global service instance
model_config_service = ModelConfigService()