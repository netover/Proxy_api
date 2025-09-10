from typing import Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field, validator

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

    @validator('messages')
    def validate_messages(cls, v):
        for msg in v:
            if 'role' not in msg or 'content' not in msg:
                raise ValueError("Each message must have 'role' and 'content'")
        return v

    @validator('logit_bias')
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

    @validator('logit_bias')
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