import asyncio
from typing import Dict, List

from src.core.provider_factory import provider_factory
from src.core.unified_config import config_manager


async def get_provider_factories(cfgs: List) -> Dict[str, any]:
    """
    Deprecated: Use provider_factory.initialize_providers instead.
    This function is maintained for backward compatibility but delegates to the centralized factory.
    """
    config = config_manager.load_config()
    providers = await provider_factory.initialize_providers(config.providers)
    return {name: provider for name, provider in providers.items()}

def instantiate_providers(provider_cfgs: List) -> Dict[str, any]:
    """
    Synchronous wrapper for initialize_providers for backward compatibility.
    """
    return asyncio.run(get_provider_factories(provider_cfgs))
