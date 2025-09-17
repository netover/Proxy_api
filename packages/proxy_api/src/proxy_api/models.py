"""Data models for proxy_api package."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ModelSelectionRequest(BaseModel):
    """Request model for updating model selection."""

    selected_model: str
    editable: bool = True
    priority: int = 100
    max_tokens: Optional[int] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)


class ModelListResponse(BaseModel):
    """Response model for listing models."""

    object: str = "list"
    data: List[Dict[str, Any]]
    provider: str
    total: int
    cached: bool
    last_refresh: int


class ModelDetailResponse(BaseModel):
    """Response model for model details."""

    object: str = "model"
    data: Dict[str, Any]
    provider: str
    cached: bool
    last_refresh: int


class RefreshResponse(BaseModel):
    """Response model for refresh operations."""

    success: bool
    provider: str
    models_refreshed: int
    cache_cleared: bool
    duration_ms: float
    timestamp: int


class ModelInfoExtended(BaseModel):
    """Extended model information."""

    id: str
    created: int
    owned_by: str
    provider: str
    status: str
    capabilities: List[str]
    description: str
    last_updated: Optional[int] = None


class ProviderConfig(BaseModel):
    """Configuration for provider discovery."""

    name: str
    base_url: str
    api_key: str
