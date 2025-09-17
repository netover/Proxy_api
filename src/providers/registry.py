"""
Provider Registry - Suporte Automático a 100+ LLMs (Inspirado no LiteLLM)
Mantém compatibilidade OpenAI enquanto roteia para providers reais.
"""

import json
import yaml
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    VISION = "vision"
    TTS = "tts"
    STT = "stt"
    IMAGE = "image"


class ProviderConfig(BaseModel):
    """Configuração de um provider individual."""

    name: str  # ex: "openai/gpt-4"
    provider: str  # ex: "openai", "anthropic", "ollama"
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None  # Optional for local models
    models: List[str]  # Modelos suportados
    type: ProviderType
    payload_transformer: Optional[str] = None  # Classe para converter payloads
    rate_limit: Optional[Dict] = None  # ex: {"rpm": 60, "tpm": 40000}
    pricing: Optional[Dict] = None  # Para spend tracking
    priority: int = 1  # Para load balancing
    enabled: bool = True


class ProviderRegistry:
    """Registry centralizado de 100+ providers."""

    def __init__(self, config_path: str = "providers/registry.yaml"):
        self.providers: Dict[str, ProviderConfig] = {}
        self._load_registry(config_path)

    def _load_registry(self, config_path: str):
        """Loads provider registry from a YAML or JSON file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.endswith(".yaml"):
                    data = yaml.safe_load(f) or {}
                else:
                    data = json.load(f)

            # The YAML file has a root 'providers' key. We need the dictionary under that key.
            provider_data = data.get("providers")
            if not isinstance(provider_data, dict):
                logger.error(
                    f"'{config_path}' is missing the root 'providers' key or it's not a dictionary."
                )
                provider_data = {}

        except FileNotFoundError:
            logger.warning(
                f"Registry file not found at '{config_path}'. Using default registry."
            )
            provider_data = self._get_default_registry()
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing registry file '{config_path}': {e}")
            provider_data = {}  # Fallback to empty on parsing error

        for provider_id, config_data in provider_data.items():
            try:
                self.providers[provider_id] = ProviderConfig(**config_data)
                logger.info(
                    f"Provider carregado: {provider_id} ({config_data.get('provider')})"
                )
            except Exception as e:
                logger.error(f"Failed to load provider config for '{provider_id}': {e}")

    def _get_default_registry(self) -> Dict:
        """Registry default com providers principais (expansível para 100+)."""
        # This is a fallback if registry.yaml is not found.
        # The user's instructions will create the full YAML file.
        return {
            "openai/gpt-4o": {
                "name": "GPT-4o",
                "provider": "openai",
                "api_base": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
                "models": ["gpt-4o", "gpt-4o-mini"],
                "type": "chat",
                "rate_limit": {"rpm": 100, "tpm": 100000},
                "pricing": {"input": 0.005, "output": 0.015},
                "priority": 10,
            },
            "anthropic/claude-3-opus": {
                "name": "Claude 3 Opus",
                "provider": "anthropic",
                "api_base": "https://api.anthropic.com/v1",
                "api_key_env": "ANTHROPIC_API_KEY",
                "models": ["claude-3-opus-20240229"],
                "type": "chat",
                "payload_transformer": "AnthropicTransformer",
                "rate_limit": {"rpm": 10, "tpm": 100000},
                "pricing": {"input": 0.015, "output": 0.075},
                "priority": 9,
            },
            "ollama/llama3": {
                "name": "Ollama Llama 3",
                "provider": "ollama",
                "api_base": "http://localhost:11434/api",
                "api_key_env": None,
                "models": ["llama3", "mistral"],
                "type": "chat",
                "rate_limit": {"rpm": 1000},
                "priority": 5,
            },
        }

    def get_provider_config(self, model_name: str) -> Optional[ProviderConfig]:
        """Busca config pelo nome do model (ex: 'gpt-4o' ou 'openai/gpt-4o')."""
        # Direct match on provider_id (e.g., "openai/gpt-4o")
        if model_name in self.providers:
            return self.providers[model_name]

        # Match by model name within a provider's model list
        for provider_id, config in self.providers.items():
            if model_name in config.models:
                return config

        logger.warning(
            f"Provider config for model '{model_name}' not found in registry."
        )
        return None

    def list_models(self, provider_type: Optional[ProviderType] = None) -> List[str]:
        """Lista todos os models disponíveis."""
        models = []
        for config in self.providers.values():
            if config.enabled and (
                provider_type is None or config.type == provider_type
            ):
                # Return the full provider_id for clarity
                for model in config.models:
                    models.append(f"{config.provider}/{model}")
        return sorted(list(set(models)))

    def get_all_providers(self) -> Dict[str, ProviderConfig]:
        return self.providers


# Instância global para ser usada em toda a aplicação
registry = ProviderRegistry(config_path="providers/registry.yaml")
