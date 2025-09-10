import os
import importlib
from typing import List, Dict, Callable
from src.core.app_config import ProviderConfig
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

def get_provider_factories(cfgs: List[ProviderConfig]) -> Dict[str, Callable]:
    factories = {}
    # Filter enabled providers
    enabled_cfgs = [cfg for cfg in cfgs if cfg.enabled]
    for cfg in enabled_cfgs:
        try:
            api_key = os.getenv(cfg.api_key_env)
            if not api_key:
                logger.error(f"API key missing for provider {cfg.name}, skipping")
                continue
            module = importlib.import_module(cfg.module)
            cls = getattr(module, cfg.class_)
            factories[cfg.name] = lambda c=cfg: cls(c)
        except Exception as e:
            logger.error(f"Failed to load factory for provider {cfg.name}: {e}")
            continue
    return factories
