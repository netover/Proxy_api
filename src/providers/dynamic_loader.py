"""
Dynamic Provider Loader - Auto-importa wrappers para 100+ providers.
Inspirado no LiteLLM's providers.py, mas integrado com sua arquitetura.
"""

import importlib
import os
from typing import Optional, Dict, Any, Callable
from .registry import (
    ProviderConfig,
    registry as global_registry,
    ProviderRegistry,
)
from src.core.exceptions import ProviderNotFoundError
from src.core.logging import logger


class DynamicProviderLoader:
    """Carrega providers dinamicamente baseado no registry."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.loaded_providers: Dict[str, Any] = {}
        self.transformers: Dict[str, Callable] = (
            self._load_builtin_transformers()
        )

    def _load_builtin_transformers(self) -> Dict[str, Callable]:
        """
        Carrega transformers built-in para providers comuns.
        Em uma implementação mais robusta, estes poderiam ser carregados dinamicamente também.
        """
        transformers = {}
        try:
            from .wrappers import (
                AnthropicTransformer,
                GoogleTransformer,
                CohereTransformer,
            )

            transformers["AnthropicTransformer"] = AnthropicTransformer()
            transformers["GoogleTransformer"] = GoogleTransformer()
            transformers["CohereTransformer"] = CohereTransformer()
            logger.info("Built-in payload transformers loaded successfully.")
        except ImportError:
            logger.warning(
                "Could not import transformers from .wrappers. This is expected if the file doesn't exist yet."
            )
        return transformers

    def load_provider_wrapper(self, provider_name: str) -> Any:
        """Carrega a classe do wrapper do provider dinamicamente."""
        if provider_name in self.loaded_providers:
            return self.loaded_providers[provider_name]

        provider_class = None
        # 1. Tentar carregar um wrapper específico de src/providers/
        try:
            module_path = f"src.providers.{provider_name}"
            module = importlib.import_module(module_path)
            # Convention: Specific provider classes are named e.g., OpenaiProvider
            provider_class = getattr(
                module, f"{provider_name.title()}Provider"
            )
            logger.info(
                f"Loaded specific wrapper for provider '{provider_name}'"
            )
        except (ImportError, AttributeError):
            # 2. Se falhar, usar o wrapper genérico OpenAI-compatível
            try:
                from .wrappers import GenericOpenAIWrapper

                provider_class = GenericOpenAIWrapper
                logger.debug(
                    f"Using GenericOpenAIWrapper for provider '{provider_name}'"
                )
            except ImportError:
                logger.error(
                    "GenericOpenAIWrapper not found. Cannot fall back."
                )
                raise ProviderNotFoundError(
                    f"Wrapper for provider '{provider_name}' not found and fallback failed."
                )

        self.loaded_providers[provider_name] = provider_class
        return provider_class

    def get_client(self, model_name: str) -> Any:
        """Retorna um client configurado para o model especificado."""
        config = self.registry.get_provider_config(model_name)
        if not config:
            raise ProviderNotFoundError(
                f"Model '{model_name}' não encontrado no registry"
            )

        ProviderWrapper = self.load_provider_wrapper(config.provider)

        # Obter a chave de API do ambiente
        api_key = os.getenv(config.api_key_env) if config.api_key_env else None

        # Instanciar o wrapper com a configuração necessária
        client_instance = ProviderWrapper(
            api_key=api_key, base_url=config.api_base
        )

        # Aplicar o transformer se um estiver especificado na configuração
        if config.payload_transformer:
            if config.payload_transformer in self.transformers:
                client_instance.set_transformer(
                    self.transformers[config.payload_transformer]
                )
                logger.info(
                    f"Applied transformer '{config.payload_transformer}' to provider '{config.provider}'"
                )
            else:
                logger.warning(
                    f"Transformer '{config.payload_transformer}' not found for provider '{config.provider}'"
                )

        return client_instance


# Instância global que usa o registry global
loader = DynamicProviderLoader(global_registry)
