import yaml
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from models import Config, ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from providers import OpenAIProvider, AnthropicProvider, Provider
import time
import httpx
from fastapi import HTTPException

# Load environment variables from .env file
load_dotenv()

# Load configuration
def load_config(path: str) -> Config:
    with open(path, 'r') as f:
        config_data = yaml.safe_load(f)
    return Config(**config_data)

config = load_config('config.yaml')

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "PROXY_API is running."}

# A mapping from provider type to provider class
PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    provider_configs = [p for p in config.providers if request.model in p.models]

    if not provider_configs:
        raise HTTPException(status_code=400, detail=f"Model '{request.model}' not supported by any provider.")

    for provider_config in provider_configs:
        provider_class = PROVIDER_CLASSES.get(provider_config.type)
        if not provider_class:
            print(f"Provider type '{provider_config.type}' not supported.")
            continue

        try:
            provider = provider_class(
                name=provider_config.name,
                api_key_env=provider_config.api_key_env,
                base_url=provider_config.base_url,
            )

            response = await provider.create_completion(request)

            if isinstance(provider, AnthropicProvider):
                return provider.transform_response(response, request)
            else:
                return response.json()

        except httpx.HTTPStatusError as e:
            print(f"Error from provider '{provider_config.name}': {e}")
            continue
        except httpx.RequestError as e:
            print(f"Request to provider '{provider_config.name}' failed: {e}")
            continue
        except ValueError as e:
            print(f"Configuration error for provider '{provider_config.name}': {e}")
            continue

    raise HTTPException(status_code=500, detail="All providers failed to process the request.")
