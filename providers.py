import httpx
import os
import json
from abc import ABC, abstractmethod
from models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage

class Provider(ABC):
    def __init__(self, name: str, api_key_env: str, base_url: str):
        self.name = name
        self.api_key = os.getenv(api_key_env)
        self.base_url = base_url
        if not self.api_key:
            raise ValueError(f"API key for provider '{self.name}' not found in environment variables.")

    @abstractmethod
    async def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        pass

class OpenAIProvider(Provider):
    async def create_completion(self, request: ChatCompletionRequest) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        request_dict = request.dict(exclude_unset=True)
        if 'extra' in request_dict:
            del request_dict['extra']

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=request_dict,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            return response

class AnthropicProvider(Provider):
    async def create_completion(self, request: ChatCompletionRequest) -> httpx.Response:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        # Transform the request to the Anthropic format
        anthropic_request = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "max_tokens": request.max_tokens if request.max_tokens else 1024, # Anthropic requires max_tokens
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json=anthropic_request,
                headers=headers,
                timeout=60,
            )
            response.raise_for_status()
            return response

    def transform_response(self, response: httpx.Response, original_request: ChatCompletionRequest) -> ChatCompletionResponse:
        anthropic_response = response.json()
        return ChatCompletionResponse(
            id=anthropic_response["id"],
            object="chat.completion",
            created=int(response.headers.get("date", 0)), # Not ideal, but Anthropic doesn't provide a created timestamp
            model=original_request.model,
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": anthropic_response["content"][0]["text"],
                    },
                    "finish_reason": anthropic_response["stop_reason"],
                }
            ],
            usage=anthropic_response.get("usage"),
        )
