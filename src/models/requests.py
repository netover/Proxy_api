from typing import Dict, Any, Union, Optional, List
from pydantic import BaseModel, Field

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

class EmbeddingRequest(BaseModel):
    """Pydantic model for embeddings request"""
    model: str = Field(..., min_length=1)
    input: Union[str, List[str]] = Field(..., min_length=1)
    user: Optional[str] = None