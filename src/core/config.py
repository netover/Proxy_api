import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator
import yaml

class Settings(BaseSettings):
    """Application settings with validation and environment support"""
    
    # App Configuration
    app_name: str = "LLM Proxy API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration  
    host: str = "127.0.0.1"
    port: int = 8000
    
    # Security
    api_key_header: str = "X-API-Key"
    allowed_origins: List[str] = ["*"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Timeouts
    client_timeout: int = 60
    provider_timeout: int = 30
    
    # Paths
    config_file: Path = Path("config.yaml")
    log_file: Path = Path("logs/proxy_api.log")
    
    @validator('config_file')
    def validate_config_file(cls, v):
        if not v.exists():
            raise ValueError(f"Configuration file {v} not found")
        return v
    
    class Config:
        env_prefix = "PROXY_API_"
        case_sensitive = False
        env_file = ".env"

settings = Settings()
