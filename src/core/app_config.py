import yaml
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, validator
from src.core.config import settings

class ProviderConfig(BaseModel):
    """Configuration for a single provider"""
    name: str
    type: str
    base_url: str
    api_key_env: str
    models: List[str]
    enabled: bool = True
    priority: int = 100
    timeout: int = 30
    rate_limit: int = 1000  # requests per hour
    
    @validator('priority')
    def validate_priority(cls, v):
        if v < 1:
            raise ValueError('Priority must be greater than 0')
        return v

class AppConfig(BaseModel):
    """Main application configuration"""
    providers: List[ProviderConfig]
    
    @validator('providers')
    def validate_providers(cls, v):
        if not v:
            raise ValueError('At least one provider must be configured')
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
