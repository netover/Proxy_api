import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator, Field, HttpUrl
from src.core.config import settings

class ProviderConfig(BaseModel):
    """Configuration for a single provider"""
    name: str = Field(..., description="Unique name for the provider")
    type: str = Field(..., description="Provider type (openai, anthropic, etc.)")
    base_url: HttpUrl = Field(..., description="Base URL for the provider API")
    api_key_env: str = Field(..., description="Environment variable name for API key")
    models: List[str] = Field(..., min_items=1, description="List of supported models")
    enabled: bool = Field(True, description="Whether this provider is enabled")
    priority: int = Field(100, ge=1, le=1000, description="Provider priority (lower = higher priority)")
    timeout: int = Field(30, ge=1, le=300, description="Request timeout in seconds")
    rate_limit: int = Field(1000, ge=1, description="Rate limit requests per hour")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, le=60.0, description="Delay between retries in seconds")
    headers: Optional[Dict[str, str]] = Field(None, description="Additional headers to send")

    @field_validator('type')
    @classmethod
    def validate_provider_type(cls, v):
        supported_types = ['openai', 'anthropic', 'azure_openai', 'cohere']
        if v.lower() not in supported_types:
            raise ValueError(f'Provider type must be one of: {supported_types}')
        return v.lower()
        
    @field_validator('models')
    @classmethod
    def validate_models(cls, v):
        if not v:
            raise ValueError('At least one model must be specified')
        return list(set(v))  # Remove duplicates

class AppConfig(BaseModel):
    """Main application configuration"""
    providers: List[ProviderConfig] = Field(..., min_items=1)

    @field_validator('providers')
    @classmethod
    def validate_providers(cls, v):
        if not v:
            raise ValueError('At least one provider must be configured')

        # Check for duplicate names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError('Provider names must be unique')

        # Check for duplicate priorities
        priorities = [p.priority for p in v]
        if len(priorities) != len(set(priorities)):
            raise ValueError('Provider priorities must be unique')

        return v
            
def load_config(config_path: Path = None) -> AppConfig:
    """Load and validate configuration from YAML file"""
    if config_path is None:
        config_path = settings.config_file
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file {config_path} not found")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return AppConfig(**config_data)

# Global config instance
config: AppConfig = None

def init_config():
    """Initialize global config instance"""
    global config
    config = load_config()
