from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = Field(..., min_length=1)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("Content cannot be empty or just whitespace.")
        return v

    def __getitem__(self, key):
        """Make ChatMessage subscriptable for testing."""
        if key == "role":
            return self.role
        elif key == "content":
            return self.content
        raise KeyError(key)

    def __contains__(self, key):
        """Make ChatMessage checkable for testing."""
        return key in ["role", "content"]

class ChatCompletionRequest(BaseModel):
    """Pydantic model for chat completions request"""

    model: str = Field(..., min_length=1)
    messages: List[ChatMessage] = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    session_id: Optional[str] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    parallel_tool_calls: Optional[bool] = False
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None

    @field_validator("logit_bias")
    @classmethod
    def validate_logit_bias(cls, v):
        if v:
            for k in v:
                if not (-100 <= v[k] <= 100):
                    raise ValueError("Logit bias values must be between -100 and 100")
        return v


class TextCompletionRequest(BaseModel):
    """Pydantic model for text completions request"""

    model: str = Field(..., min_length=1)
    prompt: Union[str, List[str]] = Field(..., min_length=1)
    max_tokens: Optional[int] = Field(None, ge=1)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    n: Optional[int] = Field(1, ge=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    suffix: Optional[str] = None
    best_of: Optional[int] = Field(1, ge=1)
    logprobs: Optional[int] = Field(None, ge=0, le=20)
    echo: Optional[bool] = False

    @field_validator("logit_bias")
    @classmethod
    def validate_logit_bias(cls, v):
        if v:
            for k in v:
                if not (-100 <= v[k] <= 100):
                    raise ValueError("Logit bias values must be between -100 and 100")
        return v


class EmbeddingRequest(BaseModel):
    """Pydantic model for embeddings request"""

    model: str = Field(..., min_length=1)
    input: Union[str, List[str]] = Field(..., min_length=1)
    user: Optional[str] = None
    encoding_format: Optional[str] = "float"

    @field_validator("input")
    @classmethod
    def validate_input(cls, v):
        if isinstance(v, list) and not v:
            raise ValueError("Input list cannot be empty.")
        if isinstance(v, str) and not v.strip():
            raise ValueError("Input string cannot be empty or just whitespace.")
        return v


class ImageGenerationRequest(BaseModel):
    """Pydantic model for image generation request"""

    model: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1, description="The text prompt for image generation.")
    n: Optional[int] = Field(1, ge=1, le=10)
    size: Optional[str] = Field("1024x1024", pattern=r"^\d+x\d+$")
    quality: Optional[str] = Field("standard", pattern=r"^(standard|hd)$")
    style: Optional[str] = Field("vivid", pattern=r"^(vivid|natural)$")
    response_format: Optional[str] = Field("url", pattern=r"^(url|b64_json)$")
    user: Optional[str] = None

    @field_validator("n")
    @classmethod
    def validate_n(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError("n must be between 1 and 10")
        return v

    @field_validator("size")
    @classmethod
    def validate_size(cls, v):
        if v is not None:
            # Common image sizes
            valid_sizes = {
                "256x256",
                "512x512",
                "1024x1024",
                "1792x1024",
                "1024x1792",
            }
            if v not in valid_sizes:
                raise ValueError(f"size must be one of: {', '.join(valid_sizes)}")


# Model Management Request/Response Models


class ModelSelectionRequest(BaseModel):
    """Request model for updating model selection configuration"""

    selected_model: str = Field(
        ..., min_length=1, description="The model ID to select as primary"
    )
    editable: bool = Field(
        True, description="Whether the model selection can be edited by users"
    )
    priority: Optional[int] = Field(
        None, ge=1, le=10, description="Priority level for this model (1-10)"
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, description="Maximum tokens override for this model"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Temperature override for this model"
    )

    @field_validator("selected_model")
    @classmethod
    def validate_model_id(cls, v):
        if not v.strip():
            raise ValueError("Model ID cannot be empty or whitespace")
        return v.strip()


class ModelInfoExtended(BaseModel):
    """Extended model information including provider-specific details"""

    id: str = Field(..., description="Unique model identifier")
    object: str = Field("model", description="Object type, always 'model'")
    created: int = Field(..., description="Unix timestamp of model creation")
    owned_by: str = Field(..., description="Organization that owns the model")
    provider: str = Field(
        ..., description="Provider name (e.g., 'openai', 'anthropic')"
    )
    status: str = Field(
        "active",
        description="Model status: active, deprecated, or discontinued",
    )
    capabilities: List[str] = Field(
        default_factory=list, description="List of supported capabilities"
    )
    context_window: Optional[int] = Field(
        None, description="Maximum context window size"
    )
    max_tokens: Optional[int] = Field(None, description="Maximum output tokens")
    pricing: Optional[Dict[str, float]] = Field(
        None, description="Pricing information per 1K tokens"
    )
    description: Optional[str] = Field(None, description="Human-readable description")
    version: Optional[str] = Field(None, description="Model version identifier")
    last_updated: Optional[int] = Field(None, description="Last update timestamp")


class ModelListResponse(BaseModel):
    """Response model for listing models"""

    object: str = Field("list", description="Object type, always 'list'")
    data: List[ModelInfoExtended] = Field(
        ..., description="List of model information objects"
    )
    provider: str = Field(..., description="Provider name for these models")
    total: int = Field(..., description="Total number of models")
    cached: bool = Field(True, description="Whether this data came from cache")
    last_refresh: Optional[int] = Field(
        None, description="Last cache refresh timestamp"
    )


class ModelDetailResponse(BaseModel):
    """Response model for detailed model information"""

    object: str = Field("model", description="Object type, always 'model'")
    data: ModelInfoExtended = Field(..., description="Detailed model information")
    provider: str = Field(..., description="Provider name")
    cached: bool = Field(True, description="Whether this data came from cache")
    last_refresh: Optional[int] = Field(
        None, description="Last cache refresh timestamp"
    )


class RefreshResponse(BaseModel):
    """Response model for cache refresh operations"""

    success: bool = Field(..., description="Whether the refresh was successful")
    provider: str = Field(..., description="Provider name")
    models_refreshed: int = Field(..., description="Number of models refreshed")
    cache_cleared: bool = Field(..., description="Whether cache was cleared")
    duration_ms: float = Field(
        ..., description="Duration of refresh operation in milliseconds"
    )
    timestamp: int = Field(..., description="Unix timestamp of refresh completion")
