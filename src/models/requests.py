from typing import Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field, field_validator

class ChatCompletionRequest(BaseModel):
    """Pydantic model for chat completions request"""
    model: str = Field(..., min_length=1)
    messages: List[Dict[str, Any]] = Field(..., min_length=1)
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
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    parallel_tool_calls: Optional[bool] = False
    response_format: Optional[Dict[str, Any]] = None
    seed: Optional[int] = None

    @field_validator('messages')
    @classmethod
    def validate_messages(cls, v):
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content'")
        return v

    @field_validator('logit_bias')
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

    @field_validator('logit_bias')
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

class ImageGenerationRequest(BaseModel):
    """Pydantic model for image generation request"""
    model: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    n: Optional[int] = Field(1, ge=1, le=10)
    size: Optional[str] = Field("1024x1024", pattern=r"^\d+x\d+$")
    quality: Optional[str] = Field("standard", pattern=r"^(standard|hd)$")
    style: Optional[str] = Field("vivid", pattern=r"^(vivid|natural)$")
    response_format: Optional[str] = Field("url", pattern=r"^(url|b64_json)$")
    user: Optional[str] = None

    @field_validator('n')
    @classmethod
    def validate_n(cls, v):
        if v is not None and not (1 <= v <= 10):
            raise ValueError("n must be between 1 and 10")
        return v

    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        if v is not None:
            # Common image sizes
            valid_sizes = {"256x256", "512x512", "1024x1024", "1792x1024", "1024x1792"}
            if v not in valid_sizes:
                raise ValueError(f"size must be one of: {', '.join(valid_sizes)}")
        return v