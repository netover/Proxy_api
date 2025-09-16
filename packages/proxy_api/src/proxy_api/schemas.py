"""API schemas and data models."""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class ChatMessage(BaseModel):
    """Individual chat message."""

    role: str = Field(
        ..., description="Role of the message sender (user, assistant, system)"
    )
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Request model for chat completions."""

    model: str = Field(..., description="Model identifier")
    messages: List[ChatMessage] = Field(
        ..., description="List of chat messages"
    )
    temperature: Optional[float] = Field(
        0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, description="Maximum tokens to generate"
    )
    top_p: Optional[float] = Field(
        1.0, ge=0.0, le=1.0, description="Top-p sampling parameter"
    )
    frequency_penalty: Optional[float] = Field(
        0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: Optional[float] = Field(
        0.0, ge=-2.0, le=2.0, description="Presence penalty"
    )
    stop: Optional[Union[str, List[str]]] = Field(
        None, description="Stop sequences"
    )
    stream: Optional[bool] = Field(False, description="Stream responses")

    @validator("messages")
    def validate_messages(cls, v):
        if not v:
            raise ValueError("messages cannot be empty")
        return v

    @validator("temperature")
    def validate_temperature(cls, v):
        if v is not None and (v < 0 or v > 2):
            raise ValueError("temperature must be between 0 and 2")
        return v


class ChatChoice(BaseModel):
    """Individual chat choice."""

    index: int = Field(..., description="Choice index")
    message: ChatMessage = Field(..., description="Chat message")
    finish_reason: Optional[str] = Field(
        None, description="Reason for completion"
    )


class ChatUsage(BaseModel):
    """Token usage information."""

    prompt_tokens: int = Field(
        ..., description="Number of tokens in the prompt"
    )
    completion_tokens: int = Field(
        ..., description="Number of tokens in the completion"
    )
    total_tokens: int = Field(..., description="Total number of tokens")


class ChatResponse(BaseModel):
    """Response model for chat completions."""

    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model identifier")
    choices: List[ChatChoice] = Field(
        ..., description="List of completion choices"
    )
    usage: ChatUsage = Field(..., description="Token usage information")


class ModelInfo(BaseModel):
    """Model information."""

    id: str = Field(..., description="Model identifier")
    object: str = Field(default="model", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    owned_by: str = Field(..., description="Organization that owns the model")


class ModelsResponse(BaseModel):
    """Response model for models listing."""

    object: str = Field(default="list", description="Object type")
    data: List[ModelInfo] = Field(..., description="List of available models")


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck(BaseModel):
    """Health check response."""

    status: HealthStatus = Field(..., description="Overall health status")
    timestamp: int = Field(..., description="Unix timestamp of the check")
    version: str = Field(..., description="API version")
    uptime: float = Field(..., description="Uptime in seconds")
    checks: Dict[str, Any] = Field(
        default_factory=dict, description="Detailed health checks"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: Dict[str, Any] = Field(..., description="Error details")
    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ProviderConfig(BaseModel):
    """Provider configuration."""

    name: str = Field(..., description="Provider name")
    api_key: Optional[str] = Field(
        None, description="API key for the provider"
    )
    base_url: Optional[str] = Field(
        None, description="Base URL for the provider"
    )
    models: List[str] = Field(
        default_factory=list, description="List of supported models"
    )
    enabled: bool = Field(True, description="Whether the provider is enabled")
    priority: int = Field(0, description="Priority for provider selection")
    rate_limit: Optional[int] = Field(
        None, description="Rate limit per minute"
    )
    timeout: Optional[int] = Field(
        30, description="Request timeout in seconds"
    )


class ConfigUpdateRequest(BaseModel):
    """Request model for configuration updates."""

    providers: Optional[List[ProviderConfig]] = Field(
        None, description="Provider configurations"
    )
    settings: Optional[Dict[str, Any]] = Field(
        None, description="General settings"
    )


class ConfigResponse(BaseModel):
    """Response model for configuration."""

    providers: List[ProviderConfig] = Field(
        ..., description="Provider configurations"
    )
    settings: Dict[str, Any] = Field(..., description="General settings")
    version: str = Field(..., description="Configuration version")
    last_updated: int = Field(..., description="Unix timestamp of last update")
