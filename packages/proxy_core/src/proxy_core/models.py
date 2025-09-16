"""Data models for proxy_core package."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class ProviderType(str, Enum):
    """Supported provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    BLACKBOX = "blackbox"
    OPENROUTER = "openrouter"
    COHERE = "cohere"
    AZURE_OPENAI = "azure_openai"


class ModelInfo(BaseModel):
    """Information about a model."""

    id: str
    name: str
    provider: str
    type: str = "chat"
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    supports_function_calling: bool = False
    supports_vision: bool = False
    pricing: Optional[Dict[str, float]] = None
    context_window: Optional[int] = None


class ProviderConfig(BaseModel):
    """Configuration for a provider."""

    name: str
    type: ProviderType
    api_key_env: str
    base_url: Optional[str] = None
    models: List[str] = []
    priority: int = 100
    enabled: bool = True
    forced: bool = False
    timeout: float = 30.0
    max_keepalive_connections: int = 100
    max_connections: int = 1000
    keepalive_expiry: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    custom_headers: Dict[str, str] = {}
    rate_limit: Optional[int] = None
