import json
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .logging import ContextualLogger

logger = ContextualLogger(__name__)


class ModelSelection(BaseModel):
    """Represents a model selection for a specific provider"""
    provider_name: str = Field(..., description="Name of the provider")
    model_name: str = Field(..., description="Name of the selected model")
    editable: bool = Field(default=True, description="Whether this selection can be modified")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ModelConfigManager:
    """Manages persistent model selections across providers"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config")
        self.config_file = self.config_dir / "model_selections.json"
        self._selections: Dict[str, ModelSelection] = {}
        self._lock = threading.RLock()
        self._ensure_config_dir()
        self._load_selections()
    
    def _ensure_config_dir(self) -> None:
        """Ensure the config directory exists"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_selections(self) -> None:
        """Load model selections from persistent storage"""
        with self._lock:
            if not self.config_file.exists():
                self._selections = {}
                return
            
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._selections = {}
                for provider_name, selection_data in data.items():
                    # Handle legacy format without datetime
                    if isinstance(selection_data, str):
                        # Old format: just model name
                        self._selections[provider_name] = ModelSelection(
                            provider_name=provider_name,
                            model_name=selection_data,
                            editable=True
                        )
                    else:
                        # New format: full ModelSelection object
                        # Parse datetime if present
                        last_updated = selection_data.get('last_updated')
                        if last_updated:
                            try:
                                last_updated = datetime.fromisoformat(last_updated)
                            except (ValueError, TypeError):
                                last_updated = datetime.utcnow()
                        
                        self._selections[provider_name] = ModelSelection(
                            provider_name=provider_name,
                            model_name=selection_data['model_name'],
                            editable=selection_data.get('editable', True),
                            last_updated=last_updated or datetime.utcnow()
                        )
                        
            except (json.JSONDecodeError, KeyError, OSError) as e:
                # If file is corrupted, backup and start fresh
                backup_file = self.config_file.with_suffix('.json.backup')
                try:
                    if self.config_file.exists():
                        import shutil
                        shutil.copy2(self.config_file, backup_file)
                except OSError:
                    pass
                self._selections = {}
    
    def _save_selections(self) -> None:
        """Save model selections to persistent storage"""
        with self._lock:
            try:
                # Create backup of existing file
                if self.config_file.exists():
                    backup_file = self.config_file.with_suffix('.json.backup')
                    import shutil
                    shutil.copy2(self.config_file, backup_file)
                
                # Write new file
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    # Convert to serializable format
                    data = {}
                    for provider_name, selection in self._selections.items():
                        data[provider_name] = {
                            'model_name': selection.model_name,
                            'editable': selection.editable,
                            'last_updated': selection.last_updated.isoformat()
                        }
                    
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            except OSError as e:
                raise RuntimeError(f"Failed to save model selections: {e}")
    
    def get_model_selection(self, provider_name: str) -> Optional[ModelSelection]:
        """Get the model selection for a specific provider"""
        with self._lock:
            return self._selections.get(provider_name)
    
    def set_model_selection(self, provider_name: str, model_name: str, editable: bool = True) -> ModelSelection:
        """Set the model selection for a specific provider"""
        with self._lock:
            selection = ModelSelection(
                provider_name=provider_name,
                model_name=model_name,
                editable=editable
            )
            self._selections[provider_name] = selection
            self._save_selections()
            return selection
    
    def update_model_selection(self, provider_name: str, model_name: str) -> Optional[ModelSelection]:
        """Update an existing model selection if it's editable"""
        with self._lock:
            existing = self._selections.get(provider_name)
            if existing and not existing.editable:
                return None
            
            selection = ModelSelection(
                provider_name=provider_name,
                model_name=model_name,
                editable=existing.editable if existing else True
            )
            self._selections[provider_name] = selection
            self._save_selections()
            return selection
    
    def remove_model_selection(self, provider_name: str) -> bool:
        """Remove a model selection for a specific provider"""
        with self._lock:
            if provider_name in self._selections:
                existing = self._selections[provider_name]
                if not existing.editable:
                    return False
                
                del self._selections[provider_name]
                self._save_selections()
                return True
            return False
    
    def get_all_selections(self) -> Dict[str, ModelSelection]:
        """Get all model selections"""
        with self._lock:
            return self._selections.copy()
    
    def get_editable_selections(self) -> Dict[str, ModelSelection]:
        """Get only editable model selections"""
        with self._lock:
            return {
                name: selection 
                for name, selection in self._selections.items() 
                if selection.editable
            }
    
    def clear_all_selections(self, force: bool = False) -> int:
        """Clear all model selections"""
        with self._lock:
            if not force:
                # Only clear editable selections
                to_remove = [
                    name for name, selection in self._selections.items()
                    if selection.editable
                ]
            else:
                # Clear all selections
                to_remove = list(self._selections.keys())
            
            for name in to_remove:
                del self._selections[name]
            
            if to_remove:
                self._save_selections()
            
            return len(to_remove)
    
    def is_model_selected(self, provider_name: str) -> bool:
        """Check if a model is selected for a provider"""
        with self._lock:
            return provider_name in self._selections
    
    def get_selected_models(self) -> Dict[str, str]:
        """Get a simple mapping of provider names to selected model names"""
        with self._lock:
            return {
                name: selection.model_name 
                for name, selection in self._selections.items()
            }
    
    @contextmanager
    def atomic_update(self):
        """Context manager for atomic updates to multiple selections"""
        with self._lock:
            # Create a temporary copy
            old_selections = self._selections.copy()
            try:
                yield self
                # Save only if no exception occurred
                self._save_selections()
            except (OSError, ValueError, RuntimeError) as e:
                # Rollback on file operation, data validation, or runtime errors
                logger.error(f"Atomic update failed, rolling back: {e}")
                self._selections = old_selections
                raise
    
    def reload(self) -> None:
        """Force reload from disk (for hot-reloading)"""
        with self._lock:
            self._load_selections()
    
    def get_config_path(self) -> Path:
        """Get the path to the configuration file"""
        return self.config_file

# Global instance
model_config_manager = ModelConfigManager()