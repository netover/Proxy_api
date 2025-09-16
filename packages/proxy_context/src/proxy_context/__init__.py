"""
Proxy Context - Context management and caching components for LLM Proxy.

This package provides:
- Context condensation and summarization
- Smart caching with TTL and memory management
- Model discovery caching
- Memory optimization utilities
"""

__version__ = "1.0.0"
__author__ = "ProxyAPI Team"
__email__ = "team@proxyapi.dev"

from .context_condenser import ContextCondenser
from .smart_cache import SmartCache, get_response_cache, get_summary_cache
from .model_cache import ModelCache
from .memory_manager import MemoryManager, get_memory_manager
from .feature_flags import (
    FeatureFlagManager,
    get_feature_flag_manager,
    is_feature_enabled,
    enable_feature_flag,
    disable_feature_flag,
    CACHE_FEATURE_FLAGS,
)

__all__ = [
    "ContextCondenser",
    "SmartCache",
    "get_response_cache",
    "get_summary_cache",
    "ModelCache",
    "MemoryManager",
    "get_memory_manager",
    "FeatureFlagManager",
    "get_feature_flag_manager",
    "is_feature_enabled",
    "enable_feature_flag",
    "disable_feature_flag",
    "CACHE_FEATURE_FLAGS",
]
