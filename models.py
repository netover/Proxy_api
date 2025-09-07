from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Provider Configuration Models
class ProviderConfig(BaseModel):
    name: str
    type: str  # 'openai' or 'anthropic'
    api_key_env: str
    base_url: str
    models: List[str]

class Config(BaseModel):
    providers: List[ProviderConfig]

# OpenAI-compatible Models

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[List[str]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    # Adding a catch-all for other potential parameters
    extra: Dict[str, Any] = Field(default_factory=dict)


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Optional[Dict[str, int]] = None
