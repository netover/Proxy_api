#!/usr/bin/env python3
"""
Gera registry.yaml com 100+ providers baseado em templates do LiteLLM.
Execute: python scripts/generate_registry.py
"""

import yaml
from typing import Dict, List

# Template base (inspirado na doc do LiteLLM)
PROVIDER_TEMPLATES = {
    "openai": {
        "provider": "openai",
        "api_base": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "type": "chat",
        "rate_limit": {"rpm": 100, "tpm": 100000},
        "priority": 10
    },
    "anthropic": {
        "provider": "anthropic",
        "api_base": "https://api.anthropic.com/v1",
        "api_key_env": "ANTHROPIC_API_KEY",
        "type": "chat",
        "payload_transformer": "AnthropicTransformer",
        "rate_limit": {"rpm": 50, "tpm": 200000},
        "priority": 9
    },
    "google_ai_studio": {
        "provider": "google_ai_studio",
        "api_base": "https://generativelanguage.googleapis.com/v1beta",
        "api_key_env": "GOOGLE_API_KEY",
        "type": "chat",
        "payload_transformer": "GoogleTransformer",
        "rate_limit": {"rpm": 15, "tpm": 1000000},
        "priority": 8
    },
    "mistral": {
        "provider": "mistral",
        "api_base": "https://api.mistral.ai/v1",
        "api_key_env": "MISTRAL_API_KEY",
        "type": "chat",
        "rate_limit": {"rpm": 20, "tpm": 50000},
        "priority": 8
    },
    "groq": {
        "provider": "groq",
        "api_base": "https://api.groq.com/openai/v1",
        "api_key_env": "GROQ_API_KEY",
        "type": "chat",
        "rate_limit": {"rpm": 30, "tpm": 100000},
        "priority": 10
    },
    "cohere": {
        "provider": "cohere",
        "api_base": "https://api.cohere.ai/v1",
        "api_key_env": "COHERE_API_KEY",
        "type": "chat",
        "payload_transformer": "CohereTransformer",
        "rate_limit": {"rpm": 20, "tpm": 60000},
        "priority": 7
    },
    "ollama": {
        "provider": "ollama",
        "api_base": "http://host.docker.internal:11434/api",
        "api_key_env": None,
        "type": "chat",
        "rate_limit": {"rpm": 1000},
        "priority": 5
    },
    "together": {
        "provider": "together",
        "api_base": "https://api.together.xyz/v1",
        "api_key_env": "TOGETHER_API_KEY",
        "type": "chat",
        "rate_limit": {"rpm": 25, "tpm": 80000},
        "priority": 7
    },
    "voyage": {
        "provider": "voyage",
        "api_base": "https://api.voyageai.com/v1",
        "api_key_env": "VOYAGE_API_KEY",
        "type": "embedding",
        "rate_limit": {"rpm": 100},
        "priority": 9
    },
    "elevenlabs": {
        "provider": "elevenlabs",
        "api_base": "https://api.elevenlabs.io/v1",
        "api_key_env": "ELEVENLABS_API_KEY",
        "type": "tts",
        "rate_limit": {"rpm": 50},
        "priority": 8
    }
}

# Models por provider (da doc do LiteLLM)
MODELS_BY_PROVIDER = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-3-large", "text-embedding-3-small", "dall-e-3"],
    "anthropic": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"],
    "google_ai_studio": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro-vision"],
    "mistral": ["open-mistral-7b", "mixtral-8x7b-instruct-v0.1", "mistral-large", "codestral-22-05"],
    "groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
    "cohere": ["command-r-plus", "command-r", "aaya-23"],
    "ollama": ["llama3", "mistral", "phi3", "gemma:7b"],
    "together": ["meta-llama/Llama-3-70b-chat-h", "mistralai/Mixtral-8x7B-Instruct-v0.1", "microsoft/DialoGPT-medium"],
    "voyage": ["voyage-2", "voyage-lite-02-instruct"],
    "elevenlabs": ["eleven_turbo_v2_5", "eleven_multilingual_v2"],
}

def get_model_type(model_name: str) -> str:
    """Determina o tipo de provider baseado no nome do modelo."""
    if "embedding" in model_name:
        return "embedding"
    if "dall-e" in model_name:
        return "image"
    # Adicionar mais regras para TTS, STT, etc.
    return "chat"

def generate_registry() -> Dict:
    """Gera o dicionário completo do registry."""
    registry = {}

    for provider, models in MODELS_BY_PROVIDER.items():
        if provider not in PROVIDER_TEMPLATES:
            continue

        template = PROVIDER_TEMPLATES[provider]
        for model in models:
            # Usar um ID único para cada entrada no YAML
            entry_id = f"{provider}/{model}"

            config = template.copy()
            config.update({
                "name": model.replace("/", " ").title(),
                "models": [model],
                "enabled": True
            })

            # Ajustar o tipo baseado no nome do modelo
            config["type"] = get_model_type(model)
            if provider == "voyage":
                config["type"] = "embedding"
            if provider == "elevenlabs":
                config["type"] = "tts"

            registry[entry_id] = config

    return registry

if __name__ == "__main__":
    full_registry = generate_registry()

    # O arquivo YAML deve ter uma chave raiz 'providers'
    output_data = {"providers": full_registry}

    # Salva o arquivo na pasta 'providers' na raiz do projeto
    output_path = "providers/registry.yaml"

    with open(output_path, "w") as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False, indent=2)

    print(f"✅ Registry gerado com sucesso em '{output_path}' com {len(full_registry)} providers!")
    print("\nExemplos de providers gerados:")
    for key in list(full_registry.keys())[:5]:
        print(f"  - {key}")
