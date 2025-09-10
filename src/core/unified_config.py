from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator, HttpUrl
from pathlib import Path
import yaml
import os
from enum import Enum

class ProviderType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    BLACKBOX = "blackbox"
    OPENROUTER = "openrouter"
    COHERE = "cohere"

class ProviderConfig(BaseModel):
    """Unified provider configuration"""
    name: str = Field(..., min_length=1, max_length=50)
    type: ProviderType
    base_url: HttpUrl
    api_key_env: str = Field(..., regex=r'^[A-Z_][A-Z0-9_]*$')
    models: List[str] = Field(..., min_items=1, max_items=100)
    
    # Performance settings
    enabled: bool = Field(default=True)
    priority: int = Field(default=100, ge=1, le=1000)
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    rate_limit: Optional[int] = Field(default=None, ge=1)
    
    # Connection settings
    max_connections: int = Field(default=10, ge=1, le=100)
    keepalive_timeout: int = Field(default=30, ge=1, le=300)
    
    # Headers
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    
    @field_validator('models')
    @classmethod
    def validate_models(cls, v):
        # Remove duplicates while preserving order
        return list(dict.fromkeys(v))
    
    @field_validator('custom_headers')
    @classmethod
    def validate_headers(cls, v):
        # Validate header names (basic check)
        for key in v.keys():
            if not key.replace('-', '').replace('_', '').isalnum():
                raise ValueError(f"Invalid header name: {key}")
        return v

class GlobalSettings(BaseModel):
    """Global application settings"""
    # App info
    app_name: str = "LLM Proxy API"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False)
    
    # Server
    host: str = Field(default="127.0.0.1", regex=r'^[\w\.\-]+$')
    port: int = Field(default=8000, ge=1, le=65535)
    
    # Security
    api_keys: List[str] = Field(default_factory=list, min_items=1)
    api_key_header: str = Field(default="X-API-Key", regex=r'^[A-Za-z0-9\-_]+$')
    cors_origins: List[str] = Field(default=["*"])
    
    # Performance
    rate_limit_rpm: int = Field(default=1000, ge=1)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)
    request_timeout: int = Field(default=300, ge=1, le=3600)
    
    # Resilience
    circuit_breaker_threshold: int = Field(default=5, ge=1, le=50)
    circuit_breaker_timeout: int = Field(default=60, ge=1, le=3600)
    
    # Paths
    log_level: str = Field(default="INFO", regex=r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    log_file: Optional[Path] = Field(default=None)
    config_file: Path = Field(default=Path("config.yaml"))
    
    class Config:
        env_prefix = "PROXY_API_"
        case_sensitive = False
        env_file = ".env"

class ProxyConfig(BaseModel):
    """Complete proxy configuration"""
    settings: GlobalSettings
    providers: List[ProviderConfig] = Field(..., min_items=1)
    
    @field_validator('providers')
    @classmethod
    def validate_providers(cls, v):
        # Check unique names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError("Provider names must be unique")
        
        # Check unique priorities among enabled providers
        enabled_priorities = [p.priority for p in v if p.enabled]
        if len(enabled_priorities) != len(set(enabled_priorities)):
            raise ValueError("Enabled provider priorities must be unique")
        
        # Validate API keys exist
        missing_keys = []
        for provider in v:
            if provider.enabled and not os.getenv(provider.api_key_env):
                missing_keys.append(provider.api_key_env)
        
        if missing_keys:
            raise ValueError(f"Missing required environment variables: {missing_keys}")
        
        return v

class ConfigManager:
    """Centralized configuration manager with caching and validation"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self._config: Optional[ProxyConfig] = None
        self._last_modified: Optional[float] = None
    
    def load_config(self, force_reload: bool = False) -> ProxyConfig:
        """Load configuration with caching and hot-reload detection"""
        try:
            current_modified = self.config_path.stat().st_mtime
            
            # Check if reload needed
            if (not force_reload and 
                self._config is not None and 
                self._last_modified == current_modified):
                return self._config
            
            # Load from file
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Separate global settings from providers
            providers_data = config_data.pop('providers', [])
            settings_data = config_data
            
            # Create configuration
            self._config = ProxyConfig(
                settings=GlobalSettings(**settings_data),
                providers=[ProviderConfig(**p) for p in providers_data]
            )
            
            self._last_modified = current_modified
            return self._config
            
        except FileNotFoundError:
            # Create default config
            return self._create_default_config()
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    def _create_default_config(self) -> ProxyConfig:
        """Create default configuration if none exists"""
        default_config = ProxyConfig(
            settings=GlobalSettings(
                api_keys=["your-api-key-here"],
                debug=True
            ),
            providers=[
                ProviderConfig(
                    name="openai_default",
                    type=ProviderType.OPENAI,
                    base_url="https://api.openai.com/v1",
                    api_key_env="OPENAI_API_KEY",
                    models=["gpt-3.5-turbo", "gpt-4"],
                    priority=1
                )
            ]
        )
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: ProxyConfig) -> None:
        """Save configuration to file"""
        config_dict = {
            **config.settings.dict(exclude={'providers'}),
            'providers': [p.dict() for p in config.providers]
        }
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, 
                          allow_unicode=True, indent=2)
        
        # Update cache
        self._config = config
        self._last_modified = self.config_path.stat().st_mtime
    
    def get_providers_for_model(self, model: str) -> List[ProviderConfig]:
        """Get enabled providers that support the given model, sorted by priority"""
        if not self._config:
            self.load_config()
        
        providers = [
            p for p in self._config.providers
            if p.enabled and model in p.models
        ]
        
        return sorted(providers, key=lambda p: p.priority)
    
    def get_provider_by_name(self, name: str) -> Optional[ProviderConfig]:
        """Get provider by name"""
        if not self._config:
            self.load_config()
        
        return next((p for p in self._config.providers if p.name == name), None)

# Global instance
config_manager = ConfigManager()