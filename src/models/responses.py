from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str
    message: str
    target: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail


class ChatCompletionChoice(BaseModel):
    """A single chat completion choice"""
    index: int
    message: Dict[str, Any]  # Contains role and content
    finish_reason: Optional[str] = None


class ChatCompletionUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __getitem__(self, key):
        """Make ChatCompletionUsage subscriptable for testing."""
        if key == "prompt_tokens":
            return self.prompt_tokens
        elif key == "completion_tokens":
            return self.completion_tokens
        elif key == "total_tokens":
            return self.total_tokens
        raise KeyError(key)

    def __contains__(self, key):
        """Make ChatCompletionUsage checkable for testing."""
        return key in ["prompt_tokens", "completion_tokens", "total_tokens"]


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage

    class Config:
        populate_by_name = True
        extra = 'ignore'