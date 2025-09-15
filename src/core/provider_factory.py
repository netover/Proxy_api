"""
Provider Factory - Evoluído para 100+ providers via registry.
Integra dynamic loading com cache, circuit breakers e monitoring.
"""
import time
from typing import Dict, Any, Optional, List
from src.providers.registry import ProviderRegistry, ProviderConfig, registry as global_registry
from src.providers.dynamic_loader import DynamicProviderLoader, loader as global_loader
from src.core.circuit_breaker import get_circuit_breaker, CircuitBreakerOpenException
from src.core.logging import StructuredLogger
from src.core.exceptions import ProviderNotFoundError, ProviderUnavailableError

logger = StructuredLogger(__name__)

class EnhancedProviderFactory:
    """
    Factory evoluída que suporta 100+ providers dinamicamente,
    integrando-se com os sistemas existentes de circuit breaker, cache e rate limiting.
    """

    def __init__(self, registry: ProviderRegistry, loader: DynamicProviderLoader):
        self.registry = registry
        self.loader = loader
        # O cache e rate limiting são aplicados em outras camadas (e.g., controllers, wrappers)
        # mas a factory pode ser um ponto para configurar os circuit breakers.
        self._initialize_protection()

    def _initialize_protection(self):
        """
        Inicializa circuit breakers para todos os providers habilitados no registry.
        A configuração é lida do registry.
        """
        for provider_id, config in self.registry.providers.items():
            if config.enabled:
                # A função get_circuit_breaker já cria e gerencia instâncias singleton
                get_circuit_breaker(
                    name=config.provider, # Breaker por provider (e.g., "openai", "anthropic")
                    failure_threshold=config.rate_limit.get("max_failures", 5) if config.rate_limit else 5,
                    recovery_timeout=60
                )
        logger.info(f"Circuit breakers initialized for {len(self.registry.providers)} providers.")

    async def get_provider_client(self, model_name: str) -> Any:
        """
        Retorna um client de provider dinamicamente carregado e protegido por um circuit breaker.
        """
        config = self.registry.get_provider_config(model_name)
        if not config or not config.enabled:
            available_models = list(self.registry.providers.keys())[:10]
            raise ProviderNotFoundError(f"Model '{model_name}' não suportado ou desabilitado. Disponíveis (amostra): {available_models}...")
        
        provider_name = config.provider
        
        # Verificar o circuit breaker antes de tentar carregar o client
        breaker = get_circuit_breaker(provider_name)
        try:
            # O 'call' do circuit breaker agora envolve a criação do cliente
            # e a chamada ao método do cliente. Aqui, apenas verificamos o estado.
            # A lógica de 'call' será aplicada no router.
            pass # A verificação real acontece no momento da chamada da API
        except CircuitBreakerOpenException as e:
            logger.error(f"Circuit breaker para o provider '{provider_name}' está aberto.")
            raise ProviderUnavailableError(f"Provider '{provider_name}' está temporariamente indisponível.") from e

        # Carrega o client dinamicamente
        client = self.loader.get_client(model_name)

        return client, config

    async def list_all_models(self) -> List[Dict]:
        """Lista todos os 100+ models disponíveis do registry para o endpoint /v1/models."""
        models = []
        for provider_id, config in self.registry.providers.items():
            if config.enabled:
                # O id do modelo no formato OpenAI é simplesmente o nome do modelo
                for model_name in config.models:
                    models.append({
                        "id": model_name,
                        "object": "model",
                        "created": int(time.time()), # Timestamp dinâmico
                        "owned_by": config.provider,
                        "provider_id": provider_id
                    })
        # Ordena por id para consistência
        return sorted(models, key=lambda x: x["id"])

    def get_pricing(self, model_name: str) -> Optional[Dict]:
        """Retorna informações de preço para um determinado modelo para spend tracking."""
        config = self.registry.get_provider_config(model_name)
        return config.pricing if config and config.pricing else None

    def add_custom_provider(self, config_data: dict):
        """Adiciona um novo provider customizado em tempo de execução (hot-reload)."""
        try:
            config = ProviderConfig(**config_data)
            provider_id = f"{config.provider}/{config.models[0]}" # Cria um ID único
            self.registry.providers[provider_id] = config
            self._initialize_protection()  # Re-inicializa a proteção para o novo provider
            logger.info(f"Provider customizado '{provider_id}' adicionado com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao adicionar provider customizado: {e}")


# Instância global que será usada pela aplicação
provider_factory = EnhancedProviderFactory(registry=global_registry, loader=global_loader)