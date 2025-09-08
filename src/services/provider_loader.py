import os
import importlib
from typing import List
from src.config.models import ProviderConfig
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

def instantiate_providers(cfgs: List[ProviderConfig]) -> List:
    providers = []
    for cfg in sorted(cfgs, key=lambda c: c.priority):
        try:
            module = importlib.import_module(cfg.module)
            cls = getattr(module, cfg.class_)
            api_key = os.getenv(cfg.api_key_env)
            providers.append(cls(
                name=cfg.name,
                api_key=api_key,
                base_url=str(cfg.base_url),
                models=cfg.models,
                priority=cfg.priority
            ))
        except Exception as e:
            logger.error(f"Failed to load provider {cfg.name}: {e}")
            continue
    return providers
