"""
LLM Proxy API - Web Configuration Interface
Secure web-based configuration management for the LLM Proxy API.
"""

import os
import re
import json
import yaml
import shlex
import secrets
import shutil
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Flask imports
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort

# Security and configuration
from dotenv import dotenv_values, set_key
from werkzeug.security import generate_password_hash, check_password_hash

# Core imports
from src.core.config import settings
from src.core.logging import ContextualLogger
from src.services.logging import iterate_logs
from src.core.model_discovery import ModelDiscoveryService, ProviderConfig

# Constants
VALID_PROVIDERS = {'openai', 'anthropic', 'perplexity', 'grok', 'blackbox', 'openrouter', 'cohere'}
ENV_VAR_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$')
PROVIDER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

ALLOWED_ENV_VARS = frozenset({
    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GROK_API_KEY', 'BLACKBOX_API_KEY',
    'OPENROUTER_API_KEY', 'PERPLEXITY_API_KEY', 'COHERE_API_KEY',
    'PROXY_API_PORT', 'PROXY_API_API_KEY_HEADER'
})

# Configuration paths
CONFIG_PATH = Path(__file__).parent / 'config.yaml'
ENV_PATH = Path(__file__).parent / '.env'
SECRET_KEY_PATH = Path(__file__).parent / '.flask_secret_key'

# --- App Initialization ---

app = Flask(__name__)
logger = ContextualLogger(__name__)
from inspect import signature as _mutmut_signature
from typing import Annotated
from typing import Callable
from typing import ClassVar


MutantDict = Annotated[dict[str, Callable], "Mutant"]


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None):
    """Forward call to original or mutated function, depending on the environment"""
    import os
    mutant_under_test = os.environ['MUTANT_UNDER_TEST']
    if mutant_under_test == 'fail':
        from mutmut.__main__ import MutmutProgrammaticFailException
        raise MutmutProgrammaticFailException('Failed programmatically')      
    elif mutant_under_test == 'stats':
        from mutmut.__main__ import record_trampoline_hit
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__)
        result = orig(*call_args, **call_kwargs)
        return result
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_'
    if not mutant_under_test.startswith(prefix):
        result = orig(*call_args, **call_kwargs)
        return result
    mutant_name = mutant_under_test.rpartition('.')[-1]
    if self_arg:
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs)
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs)
    return result

def x_get_persistent_secret_key__mutmut_orig() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_1() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = None
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_2() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv(None)
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_3() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('XXFLASK_SECRET_KEYXX')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_4() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('flask_secret_key')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_5() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info(None)
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_6() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("XXGenerating new persistent secret key.XX")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_7() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_8() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("GENERATING NEW PERSISTENT SECRET KEY.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_9() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = None
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_10() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(None)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_11() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(33)
    SECRET_KEY_PATH.write_text(new_key)
    return new_key

def x_get_persistent_secret_key__mutmut_12() -> str:
    """
    Get a persistent Flask secret key.
    Reads from FLASK_SECRET_KEY env var, then .flask_secret_key file.
    Generates and saves a new key if none exist.
    """
    env_key = os.getenv('FLASK_SECRET_KEY')
    if env_key:
        return env_key

    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_text().strip()

    logger.info("Generating new persistent secret key.")
    new_key = secrets.token_hex(32)
    SECRET_KEY_PATH.write_text(None)
    return new_key

x_get_persistent_secret_key__mutmut_mutants : ClassVar[MutantDict] = {
'x_get_persistent_secret_key__mutmut_1': x_get_persistent_secret_key__mutmut_1, 
    'x_get_persistent_secret_key__mutmut_2': x_get_persistent_secret_key__mutmut_2, 
    'x_get_persistent_secret_key__mutmut_3': x_get_persistent_secret_key__mutmut_3, 
    'x_get_persistent_secret_key__mutmut_4': x_get_persistent_secret_key__mutmut_4, 
    'x_get_persistent_secret_key__mutmut_5': x_get_persistent_secret_key__mutmut_5, 
    'x_get_persistent_secret_key__mutmut_6': x_get_persistent_secret_key__mutmut_6, 
    'x_get_persistent_secret_key__mutmut_7': x_get_persistent_secret_key__mutmut_7, 
    'x_get_persistent_secret_key__mutmut_8': x_get_persistent_secret_key__mutmut_8, 
    'x_get_persistent_secret_key__mutmut_9': x_get_persistent_secret_key__mutmut_9, 
    'x_get_persistent_secret_key__mutmut_10': x_get_persistent_secret_key__mutmut_10, 
    'x_get_persistent_secret_key__mutmut_11': x_get_persistent_secret_key__mutmut_11, 
    'x_get_persistent_secret_key__mutmut_12': x_get_persistent_secret_key__mutmut_12
}

def get_persistent_secret_key(*args, **kwargs):
    result = _mutmut_trampoline(x_get_persistent_secret_key__mutmut_orig, x_get_persistent_secret_key__mutmut_mutants, args, kwargs)
    return result 

get_persistent_secret_key.__signature__ = _mutmut_signature(x_get_persistent_secret_key__mutmut_orig)
x_get_persistent_secret_key__mutmut_orig.__name__ = 'x_get_persistent_secret_key'

# Security configuration
app.config.update(
    SECRET_KEY=get_persistent_secret_key(),
    SESSION_COOKIE_SECURE=os.getenv('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
    WTF_CSRF_ENABLED=True, # Note: Manual CSRF implementation exists below
    WTF_CSRF_TIME_LIMIT=3600
)

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_orig() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_1() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_2() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning(None)
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_3() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("XXConfiguration file not found, using defaults.XX")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_4() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_5() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("CONFIGURATION FILE NOT FOUND, USING DEFAULTS.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_6() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"XXprovidersXX": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_7() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"PROVIDERS": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_8() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(None, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_9() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, None, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_10() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding=None) as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_11() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open('r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_12() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_13() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', ) as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_14() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'XXrXX', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_15() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'R', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_16() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='XXutf-8XX') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_17() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='UTF-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_18() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = None
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_19() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) and {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_20() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(None) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_21() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_22() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError(None)
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_23() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("XXInvalid config: 'providers' must be a list.XX")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_24() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_25() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("INVALID CONFIG: 'PROVIDERS' MUST BE A LIST.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_26() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get(None, []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_27() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', None):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_28() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get([]):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_29() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', ):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_30() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('XXprovidersXX', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_31() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('PROVIDERS', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_32() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_33() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(None):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_34() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k not in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_35() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['XXnameXX', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_36() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['NAME', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_37() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'XXtypeXX', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_38() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'TYPE', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_39() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'XXmodelsXX']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_40() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'MODELS']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_41() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError(None)
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_42() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("XXProvider missing required keys.XX")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_43() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_44() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("PROVIDER MISSING REQUIRED KEYS.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_45() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(None, exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_46() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=None)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_47() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_48() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", )
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_49() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=False)
        # In a real app, you might want to exit if config is critical and invalid
        return {"providers": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_50() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"XXprovidersXX": []}

# --- Pre-loaded Configuration ---

def x_load_config_once__mutmut_51() -> Dict[str, Any]:
    """Load YAML configuration once with validation, intended for app startup."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults.")
            return {"providers": []}
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list.")
        for provider in config.get('providers', []):
            if not all(k in provider for k in ['name', 'type', 'models']):
                raise ValueError("Provider missing required keys.")
        return config
    except (yaml.YAMLError, ValueError) as e:
        logger.error(f"Failed to load or validate config.yaml: {e}", exc_info=True)
        # In a real app, you might want to exit if config is critical and invalid
        return {"PROVIDERS": []}

x_load_config_once__mutmut_mutants : ClassVar[MutantDict] = {
'x_load_config_once__mutmut_1': x_load_config_once__mutmut_1, 
    'x_load_config_once__mutmut_2': x_load_config_once__mutmut_2, 
    'x_load_config_once__mutmut_3': x_load_config_once__mutmut_3, 
    'x_load_config_once__mutmut_4': x_load_config_once__mutmut_4, 
    'x_load_config_once__mutmut_5': x_load_config_once__mutmut_5, 
    'x_load_config_once__mutmut_6': x_load_config_once__mutmut_6, 
    'x_load_config_once__mutmut_7': x_load_config_once__mutmut_7, 
    'x_load_config_once__mutmut_8': x_load_config_once__mutmut_8, 
    'x_load_config_once__mutmut_9': x_load_config_once__mutmut_9, 
    'x_load_config_once__mutmut_10': x_load_config_once__mutmut_10, 
    'x_load_config_once__mutmut_11': x_load_config_once__mutmut_11, 
    'x_load_config_once__mutmut_12': x_load_config_once__mutmut_12, 
    'x_load_config_once__mutmut_13': x_load_config_once__mutmut_13, 
    'x_load_config_once__mutmut_14': x_load_config_once__mutmut_14, 
    'x_load_config_once__mutmut_15': x_load_config_once__mutmut_15, 
    'x_load_config_once__mutmut_16': x_load_config_once__mutmut_16, 
    'x_load_config_once__mutmut_17': x_load_config_once__mutmut_17, 
    'x_load_config_once__mutmut_18': x_load_config_once__mutmut_18, 
    'x_load_config_once__mutmut_19': x_load_config_once__mutmut_19, 
    'x_load_config_once__mutmut_20': x_load_config_once__mutmut_20, 
    'x_load_config_once__mutmut_21': x_load_config_once__mutmut_21, 
    'x_load_config_once__mutmut_22': x_load_config_once__mutmut_22, 
    'x_load_config_once__mutmut_23': x_load_config_once__mutmut_23, 
    'x_load_config_once__mutmut_24': x_load_config_once__mutmut_24, 
    'x_load_config_once__mutmut_25': x_load_config_once__mutmut_25, 
    'x_load_config_once__mutmut_26': x_load_config_once__mutmut_26, 
    'x_load_config_once__mutmut_27': x_load_config_once__mutmut_27, 
    'x_load_config_once__mutmut_28': x_load_config_once__mutmut_28, 
    'x_load_config_once__mutmut_29': x_load_config_once__mutmut_29, 
    'x_load_config_once__mutmut_30': x_load_config_once__mutmut_30, 
    'x_load_config_once__mutmut_31': x_load_config_once__mutmut_31, 
    'x_load_config_once__mutmut_32': x_load_config_once__mutmut_32, 
    'x_load_config_once__mutmut_33': x_load_config_once__mutmut_33, 
    'x_load_config_once__mutmut_34': x_load_config_once__mutmut_34, 
    'x_load_config_once__mutmut_35': x_load_config_once__mutmut_35, 
    'x_load_config_once__mutmut_36': x_load_config_once__mutmut_36, 
    'x_load_config_once__mutmut_37': x_load_config_once__mutmut_37, 
    'x_load_config_once__mutmut_38': x_load_config_once__mutmut_38, 
    'x_load_config_once__mutmut_39': x_load_config_once__mutmut_39, 
    'x_load_config_once__mutmut_40': x_load_config_once__mutmut_40, 
    'x_load_config_once__mutmut_41': x_load_config_once__mutmut_41, 
    'x_load_config_once__mutmut_42': x_load_config_once__mutmut_42, 
    'x_load_config_once__mutmut_43': x_load_config_once__mutmut_43, 
    'x_load_config_once__mutmut_44': x_load_config_once__mutmut_44, 
    'x_load_config_once__mutmut_45': x_load_config_once__mutmut_45, 
    'x_load_config_once__mutmut_46': x_load_config_once__mutmut_46, 
    'x_load_config_once__mutmut_47': x_load_config_once__mutmut_47, 
    'x_load_config_once__mutmut_48': x_load_config_once__mutmut_48, 
    'x_load_config_once__mutmut_49': x_load_config_once__mutmut_49, 
    'x_load_config_once__mutmut_50': x_load_config_once__mutmut_50, 
    'x_load_config_once__mutmut_51': x_load_config_once__mutmut_51
}

def load_config_once(*args, **kwargs):
    result = _mutmut_trampoline(x_load_config_once__mutmut_orig, x_load_config_once__mutmut_mutants, args, kwargs)
    return result 

load_config_once.__signature__ = _mutmut_signature(x_load_config_once__mutmut_orig)
x_load_config_once__mutmut_orig.__name__ = 'x_load_config_once'

def x_load_env_once__mutmut_orig() -> Dict[str, str]:
    """Load .env file once, intended for app startup."""
    return dotenv_values(ENV_PATH)

def x_load_env_once__mutmut_1() -> Dict[str, str]:
    """Load .env file once, intended for app startup."""
    return dotenv_values(None)

x_load_env_once__mutmut_mutants : ClassVar[MutantDict] = {
'x_load_env_once__mutmut_1': x_load_env_once__mutmut_1
}

def load_env_once(*args, **kwargs):
    result = _mutmut_trampoline(x_load_env_once__mutmut_orig, x_load_env_once__mutmut_mutants, args, kwargs)
    return result 

load_env_once.__signature__ = _mutmut_signature(x_load_env_once__mutmut_orig)
x_load_env_once__mutmut_orig.__name__ = 'x_load_env_once'

# Load configurations at startup to avoid repeated disk I/O
APP_CONFIG = load_config_once()
APP_ENV_VARS = load_env_once()

def x_save_config_and_env__mutmut_orig(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_1(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = None
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_2(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = None

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_3(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = None
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_4(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 1
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_5(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = ""
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_6(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' not in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_7(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = None
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_8(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(None, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_9(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, None)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_10(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_11(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, )
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_12(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_13(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return True
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_14(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(None)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_15(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get(None) == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_16(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('XXforced_providerXX') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_17(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('FORCED_PROVIDER') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_18(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') != provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_19(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['XXnameXX']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_20(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['NAME']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_21(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = None

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_22(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['XXnameXX']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_23(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['NAME']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_24(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get(None):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_25(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('XXapi_key_valueXX'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_26(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('API_KEY_VALUE'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_27(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = None

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_28(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['XXapi_key_envXX']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_29(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['API_KEY_ENV']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_30(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['XXapi_key_valueXX']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_31(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['API_KEY_VALUE']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_32(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i = 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_33(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i -= 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_34(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 2

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_35(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = None

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_36(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['XXforcedXX'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_37(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['FORCED'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_38(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['XXnameXX'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_39(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['NAME'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_40(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] != forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_41(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_42(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash(None, "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_43(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", None)
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_44(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_45(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", )
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_46(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("XXAt least one provider is requiredXX", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_47(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("at least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_48(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("AT LEAST ONE PROVIDER IS REQUIRED", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_49(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "XXerrorXX")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_50(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "ERROR")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_51(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return True

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_52(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = None
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_53(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(None)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_54(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_55(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return True

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_56(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = None
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_57(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(None)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_58(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_59(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return True

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_60(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = None
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_61(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(None, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_62(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, None)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_63(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_64(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, )
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_65(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_66(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return True

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_67(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash(None, "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_68(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", None)
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_69(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_70(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", )
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_71(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("XXConfiguration saved successfully! Restart the API server for changes to take effect.XX", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_72(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("configuration saved successfully! restart the api server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_73(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("CONFIGURATION SAVED SUCCESSFULLY! RESTART THE API SERVER FOR CHANGES TO TAKE EFFECT.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_74(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "XXsuccessXX")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_75(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "SUCCESS")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_76(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info(None)
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_77(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("XXConfiguration saved successfullyXX")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_78(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_79(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("CONFIGURATION SAVED SUCCESSFULLY")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_80(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return False

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_81(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(None)
        flash(f"Error saving configuration: {str(e)}", "error")
        return False

def x_save_config_and_env__mutmut_82(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(None, "error")
        return False

def x_save_config_and_env__mutmut_83(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", None)
        return False

def x_save_config_and_env__mutmut_84(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash("error")
        return False

def x_save_config_and_env__mutmut_85(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", )
        return False

def x_save_config_and_env__mutmut_86(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(None)}", "error")
        return False

def x_save_config_and_env__mutmut_87(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "XXerrorXX")
        return False

def x_save_config_and_env__mutmut_88(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "ERROR")
        return False

def x_save_config_and_env__mutmut_89(form_data) -> bool:
    """Save configuration and environment variables atomically."""

    try:
        providers = []
        env_updates = {}

        # Parse providers from form data
        i = 0
        forced_provider = None
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False
            providers.append(provider_data)

            # Check if this is the forced provider
            if form_data.get('forced_provider') == provider_data['name']:
                forced_provider = provider_data['name']

            # Collect environment updates
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']

            i += 1

        # Ensure only one provider is forced
        if forced_provider:
            for provider in providers:
                provider['forced'] = (provider['name'] == forced_provider)

        if not providers:
            flash("At least one provider is required", "error")
            return False

        # Validate server settings
        server_settings = _parse_server_settings(form_data)
        if not server_settings:
            return False

        # Atomic save operations
        success = _atomic_save_config(providers)
        if not success:
            return False

        success = _atomic_save_env(env_updates, server_settings)
        if not success:
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash(f"Error saving configuration: {str(e)}", "error")
        return True

x_save_config_and_env__mutmut_mutants : ClassVar[MutantDict] = {
'x_save_config_and_env__mutmut_1': x_save_config_and_env__mutmut_1, 
    'x_save_config_and_env__mutmut_2': x_save_config_and_env__mutmut_2, 
    'x_save_config_and_env__mutmut_3': x_save_config_and_env__mutmut_3, 
    'x_save_config_and_env__mutmut_4': x_save_config_and_env__mutmut_4, 
    'x_save_config_and_env__mutmut_5': x_save_config_and_env__mutmut_5, 
    'x_save_config_and_env__mutmut_6': x_save_config_and_env__mutmut_6, 
    'x_save_config_and_env__mutmut_7': x_save_config_and_env__mutmut_7, 
    'x_save_config_and_env__mutmut_8': x_save_config_and_env__mutmut_8, 
    'x_save_config_and_env__mutmut_9': x_save_config_and_env__mutmut_9, 
    'x_save_config_and_env__mutmut_10': x_save_config_and_env__mutmut_10, 
    'x_save_config_and_env__mutmut_11': x_save_config_and_env__mutmut_11, 
    'x_save_config_and_env__mutmut_12': x_save_config_and_env__mutmut_12, 
    'x_save_config_and_env__mutmut_13': x_save_config_and_env__mutmut_13, 
    'x_save_config_and_env__mutmut_14': x_save_config_and_env__mutmut_14, 
    'x_save_config_and_env__mutmut_15': x_save_config_and_env__mutmut_15, 
    'x_save_config_and_env__mutmut_16': x_save_config_and_env__mutmut_16, 
    'x_save_config_and_env__mutmut_17': x_save_config_and_env__mutmut_17, 
    'x_save_config_and_env__mutmut_18': x_save_config_and_env__mutmut_18, 
    'x_save_config_and_env__mutmut_19': x_save_config_and_env__mutmut_19, 
    'x_save_config_and_env__mutmut_20': x_save_config_and_env__mutmut_20, 
    'x_save_config_and_env__mutmut_21': x_save_config_and_env__mutmut_21, 
    'x_save_config_and_env__mutmut_22': x_save_config_and_env__mutmut_22, 
    'x_save_config_and_env__mutmut_23': x_save_config_and_env__mutmut_23, 
    'x_save_config_and_env__mutmut_24': x_save_config_and_env__mutmut_24, 
    'x_save_config_and_env__mutmut_25': x_save_config_and_env__mutmut_25, 
    'x_save_config_and_env__mutmut_26': x_save_config_and_env__mutmut_26, 
    'x_save_config_and_env__mutmut_27': x_save_config_and_env__mutmut_27, 
    'x_save_config_and_env__mutmut_28': x_save_config_and_env__mutmut_28, 
    'x_save_config_and_env__mutmut_29': x_save_config_and_env__mutmut_29, 
    'x_save_config_and_env__mutmut_30': x_save_config_and_env__mutmut_30, 
    'x_save_config_and_env__mutmut_31': x_save_config_and_env__mutmut_31, 
    'x_save_config_and_env__mutmut_32': x_save_config_and_env__mutmut_32, 
    'x_save_config_and_env__mutmut_33': x_save_config_and_env__mutmut_33, 
    'x_save_config_and_env__mutmut_34': x_save_config_and_env__mutmut_34, 
    'x_save_config_and_env__mutmut_35': x_save_config_and_env__mutmut_35, 
    'x_save_config_and_env__mutmut_36': x_save_config_and_env__mutmut_36, 
    'x_save_config_and_env__mutmut_37': x_save_config_and_env__mutmut_37, 
    'x_save_config_and_env__mutmut_38': x_save_config_and_env__mutmut_38, 
    'x_save_config_and_env__mutmut_39': x_save_config_and_env__mutmut_39, 
    'x_save_config_and_env__mutmut_40': x_save_config_and_env__mutmut_40, 
    'x_save_config_and_env__mutmut_41': x_save_config_and_env__mutmut_41, 
    'x_save_config_and_env__mutmut_42': x_save_config_and_env__mutmut_42, 
    'x_save_config_and_env__mutmut_43': x_save_config_and_env__mutmut_43, 
    'x_save_config_and_env__mutmut_44': x_save_config_and_env__mutmut_44, 
    'x_save_config_and_env__mutmut_45': x_save_config_and_env__mutmut_45, 
    'x_save_config_and_env__mutmut_46': x_save_config_and_env__mutmut_46, 
    'x_save_config_and_env__mutmut_47': x_save_config_and_env__mutmut_47, 
    'x_save_config_and_env__mutmut_48': x_save_config_and_env__mutmut_48, 
    'x_save_config_and_env__mutmut_49': x_save_config_and_env__mutmut_49, 
    'x_save_config_and_env__mutmut_50': x_save_config_and_env__mutmut_50, 
    'x_save_config_and_env__mutmut_51': x_save_config_and_env__mutmut_51, 
    'x_save_config_and_env__mutmut_52': x_save_config_and_env__mutmut_52, 
    'x_save_config_and_env__mutmut_53': x_save_config_and_env__mutmut_53, 
    'x_save_config_and_env__mutmut_54': x_save_config_and_env__mutmut_54, 
    'x_save_config_and_env__mutmut_55': x_save_config_and_env__mutmut_55, 
    'x_save_config_and_env__mutmut_56': x_save_config_and_env__mutmut_56, 
    'x_save_config_and_env__mutmut_57': x_save_config_and_env__mutmut_57, 
    'x_save_config_and_env__mutmut_58': x_save_config_and_env__mutmut_58, 
    'x_save_config_and_env__mutmut_59': x_save_config_and_env__mutmut_59, 
    'x_save_config_and_env__mutmut_60': x_save_config_and_env__mutmut_60, 
    'x_save_config_and_env__mutmut_61': x_save_config_and_env__mutmut_61, 
    'x_save_config_and_env__mutmut_62': x_save_config_and_env__mutmut_62, 
    'x_save_config_and_env__mutmut_63': x_save_config_and_env__mutmut_63, 
    'x_save_config_and_env__mutmut_64': x_save_config_and_env__mutmut_64, 
    'x_save_config_and_env__mutmut_65': x_save_config_and_env__mutmut_65, 
    'x_save_config_and_env__mutmut_66': x_save_config_and_env__mutmut_66, 
    'x_save_config_and_env__mutmut_67': x_save_config_and_env__mutmut_67, 
    'x_save_config_and_env__mutmut_68': x_save_config_and_env__mutmut_68, 
    'x_save_config_and_env__mutmut_69': x_save_config_and_env__mutmut_69, 
    'x_save_config_and_env__mutmut_70': x_save_config_and_env__mutmut_70, 
    'x_save_config_and_env__mutmut_71': x_save_config_and_env__mutmut_71, 
    'x_save_config_and_env__mutmut_72': x_save_config_and_env__mutmut_72, 
    'x_save_config_and_env__mutmut_73': x_save_config_and_env__mutmut_73, 
    'x_save_config_and_env__mutmut_74': x_save_config_and_env__mutmut_74, 
    'x_save_config_and_env__mutmut_75': x_save_config_and_env__mutmut_75, 
    'x_save_config_and_env__mutmut_76': x_save_config_and_env__mutmut_76, 
    'x_save_config_and_env__mutmut_77': x_save_config_and_env__mutmut_77, 
    'x_save_config_and_env__mutmut_78': x_save_config_and_env__mutmut_78, 
    'x_save_config_and_env__mutmut_79': x_save_config_and_env__mutmut_79, 
    'x_save_config_and_env__mutmut_80': x_save_config_and_env__mutmut_80, 
    'x_save_config_and_env__mutmut_81': x_save_config_and_env__mutmut_81, 
    'x_save_config_and_env__mutmut_82': x_save_config_and_env__mutmut_82, 
    'x_save_config_and_env__mutmut_83': x_save_config_and_env__mutmut_83, 
    'x_save_config_and_env__mutmut_84': x_save_config_and_env__mutmut_84, 
    'x_save_config_and_env__mutmut_85': x_save_config_and_env__mutmut_85, 
    'x_save_config_and_env__mutmut_86': x_save_config_and_env__mutmut_86, 
    'x_save_config_and_env__mutmut_87': x_save_config_and_env__mutmut_87, 
    'x_save_config_and_env__mutmut_88': x_save_config_and_env__mutmut_88, 
    'x_save_config_and_env__mutmut_89': x_save_config_and_env__mutmut_89
}

def save_config_and_env(*args, **kwargs):
    result = _mutmut_trampoline(x_save_config_and_env__mutmut_orig, x_save_config_and_env__mutmut_mutants, args, kwargs)
    return result 

save_config_and_env.__signature__ = _mutmut_signature(x_save_config_and_env__mutmut_orig)
x_save_config_and_env__mutmut_orig.__name__ = 'x_save_config_and_env'


def x__parse_provider_from_form__mutmut_orig(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_1(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = None
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_2(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(None, '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_3(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', None).strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_4(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get('').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_5(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', ).strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_6(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', 'XXXX').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_7(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = None
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_8(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().upper()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_9(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(None, '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_10(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', None).strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_11(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get('').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_12(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', ).strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_13(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', 'XXXX').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_14(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = None
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_15(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().lower()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_16(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(None, '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_17(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', None).strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_18(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get('').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_19(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', ).strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_20(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', 'XXXX').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_21(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = None
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_22(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(None, '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_23(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', None).strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_24(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get('').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_25(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', ).strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_26(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', 'XXXX').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_27(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = None
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_28(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(None, '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_29(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', None).strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_30(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get('').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_31(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', ).strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_32(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', 'XXXX').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_33(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = None
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_34(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(None, '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_35(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', None).strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_36(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get('').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_37(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', ).strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_38(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', 'XXXX').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_39(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = None

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_40(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(None, '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_41(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', None).strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_42(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get('').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_43(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', ).strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_44(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', 'XXXX').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_45(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name and not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_46(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_47(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_48(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(None):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_49(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(None, "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_50(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", None)
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_51(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash("error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_52(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", )
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_53(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "XXerrorXX")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_54(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "ERROR")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_55(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_56(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(None, "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_57(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", None)
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_58(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash("error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_59(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", )
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_60(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "XXerrorXX")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_61(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "ERROR")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_62(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env and not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_63(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_64(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_65(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(None):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_66(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(None, "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_67(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", None)
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_68(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash("error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_69(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", )
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_70(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "XXerrorXX")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_71(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "ERROR")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_72(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_73(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(None, "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_74(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", None)
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_75(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash("error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_76(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", )
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_77(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "XXerrorXX")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_78(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "ERROR")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_79(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = None
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_80(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(None)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_81(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_82(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (1 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_83(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 < priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_84(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority < 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_85(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1001):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_86(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError(None)
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_87(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("XXPriority out of rangeXX")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_88(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_89(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("PRIORITY OUT OF RANGE")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_90(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(None, "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_91(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", None)
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_92(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash("error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_93(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", )
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_94(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "XXerrorXX")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_95(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "ERROR")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_96(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = None
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_97(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(None) if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_98(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split('XX,XX') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_99(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_100(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(None, "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_101(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", None)
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_102(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash("error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_103(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", )
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_104(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "XXerrorXX")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_105(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "ERROR")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_106(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'XXnameXX': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_107(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'NAME': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_108(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'XXtypeXX': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_109(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'TYPE': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_110(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'XXapi_key_envXX': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_111(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'API_KEY_ENV': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_112(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'XXapi_key_valueXX': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_113(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'API_KEY_VALUE': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_114(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'XXbase_urlXX': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_115(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'BASE_URL': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_116(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'XXmodelsXX': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_117(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'MODELS': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_118(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'XXenabledXX': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_119(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'ENABLED': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_120(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(None, 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_121(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', None) == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_122(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get('false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_123(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', ) == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_124(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'XXfalseXX') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_125(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'FALSE') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_126(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') != 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_127(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'XXtrueXX',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_128(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'TRUE',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_129(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'XXforcedXX': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_130(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'FORCED': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_131(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(None, 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_132(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', None) == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_133(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get('false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_134(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', ) == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_135(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'XXfalseXX') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_136(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'FALSE') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_137(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') != 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_138(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'XXtrueXX',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_139(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'TRUE',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_140(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'XXpriorityXX': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_141(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'PRIORITY': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_142(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(None)
        flash(f"Error parsing provider {index}", "error")
        return None


def x__parse_provider_from_form__mutmut_143(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(None, "error")
        return None


def x__parse_provider_from_form__mutmut_144(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", None)
        return None


def x__parse_provider_from_form__mutmut_145(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash("error")
        return None


def x__parse_provider_from_form__mutmut_146(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", )
        return None


def x__parse_provider_from_form__mutmut_147(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "XXerrorXX")
        return None


def x__parse_provider_from_form__mutmut_148(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    try:
        provider_name = form_data.get(f'provider_name_{index}', '').strip()
        provider_type = form_data.get(f'type_{index}', '').strip().lower()
        api_key_env = form_data.get(f'api_key_env_{index}', '').strip().upper()
        api_key_value = form_data.get(f'api_key_value_{index}', '').strip()
        models_str = form_data.get(f'models_{index}', '').strip()
        priority_str = form_data.get(f'priority_{index}', '').strip()
        base_url = form_data.get(f'base_url_{index}', '').strip()

        # Validation
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        if api_key_env not in ALLOWED_ENV_VARS:
            flash(f"Environment variable not allowed: {api_key_env}", "error")
            return None

        try:
            priority = int(priority_str)
            if not (0 <= priority <= 1000):
                raise ValueError("Priority out of range")
        except ValueError:
            flash(f"Invalid priority: {priority_str}", "error")
            return None

        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': api_key_value,
            'base_url': base_url,
            'models': models,
            'enabled': form_data.get(f'enabled_{index}', 'false') == 'true',
            'forced': form_data.get(f'forced_{index}', 'false') == 'true',
            'priority': priority
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}")
        flash(f"Error parsing provider {index}", "ERROR")
        return None

x__parse_provider_from_form__mutmut_mutants : ClassVar[MutantDict] = {
'x__parse_provider_from_form__mutmut_1': x__parse_provider_from_form__mutmut_1, 
    'x__parse_provider_from_form__mutmut_2': x__parse_provider_from_form__mutmut_2, 
    'x__parse_provider_from_form__mutmut_3': x__parse_provider_from_form__mutmut_3, 
    'x__parse_provider_from_form__mutmut_4': x__parse_provider_from_form__mutmut_4, 
    'x__parse_provider_from_form__mutmut_5': x__parse_provider_from_form__mutmut_5, 
    'x__parse_provider_from_form__mutmut_6': x__parse_provider_from_form__mutmut_6, 
    'x__parse_provider_from_form__mutmut_7': x__parse_provider_from_form__mutmut_7, 
    'x__parse_provider_from_form__mutmut_8': x__parse_provider_from_form__mutmut_8, 
    'x__parse_provider_from_form__mutmut_9': x__parse_provider_from_form__mutmut_9, 
    'x__parse_provider_from_form__mutmut_10': x__parse_provider_from_form__mutmut_10, 
    'x__parse_provider_from_form__mutmut_11': x__parse_provider_from_form__mutmut_11, 
    'x__parse_provider_from_form__mutmut_12': x__parse_provider_from_form__mutmut_12, 
    'x__parse_provider_from_form__mutmut_13': x__parse_provider_from_form__mutmut_13, 
    'x__parse_provider_from_form__mutmut_14': x__parse_provider_from_form__mutmut_14, 
    'x__parse_provider_from_form__mutmut_15': x__parse_provider_from_form__mutmut_15, 
    'x__parse_provider_from_form__mutmut_16': x__parse_provider_from_form__mutmut_16, 
    'x__parse_provider_from_form__mutmut_17': x__parse_provider_from_form__mutmut_17, 
    'x__parse_provider_from_form__mutmut_18': x__parse_provider_from_form__mutmut_18, 
    'x__parse_provider_from_form__mutmut_19': x__parse_provider_from_form__mutmut_19, 
    'x__parse_provider_from_form__mutmut_20': x__parse_provider_from_form__mutmut_20, 
    'x__parse_provider_from_form__mutmut_21': x__parse_provider_from_form__mutmut_21, 
    'x__parse_provider_from_form__mutmut_22': x__parse_provider_from_form__mutmut_22, 
    'x__parse_provider_from_form__mutmut_23': x__parse_provider_from_form__mutmut_23, 
    'x__parse_provider_from_form__mutmut_24': x__parse_provider_from_form__mutmut_24, 
    'x__parse_provider_from_form__mutmut_25': x__parse_provider_from_form__mutmut_25, 
    'x__parse_provider_from_form__mutmut_26': x__parse_provider_from_form__mutmut_26, 
    'x__parse_provider_from_form__mutmut_27': x__parse_provider_from_form__mutmut_27, 
    'x__parse_provider_from_form__mutmut_28': x__parse_provider_from_form__mutmut_28, 
    'x__parse_provider_from_form__mutmut_29': x__parse_provider_from_form__mutmut_29, 
    'x__parse_provider_from_form__mutmut_30': x__parse_provider_from_form__mutmut_30, 
    'x__parse_provider_from_form__mutmut_31': x__parse_provider_from_form__mutmut_31, 
    'x__parse_provider_from_form__mutmut_32': x__parse_provider_from_form__mutmut_32, 
    'x__parse_provider_from_form__mutmut_33': x__parse_provider_from_form__mutmut_33, 
    'x__parse_provider_from_form__mutmut_34': x__parse_provider_from_form__mutmut_34, 
    'x__parse_provider_from_form__mutmut_35': x__parse_provider_from_form__mutmut_35, 
    'x__parse_provider_from_form__mutmut_36': x__parse_provider_from_form__mutmut_36, 
    'x__parse_provider_from_form__mutmut_37': x__parse_provider_from_form__mutmut_37, 
    'x__parse_provider_from_form__mutmut_38': x__parse_provider_from_form__mutmut_38, 
    'x__parse_provider_from_form__mutmut_39': x__parse_provider_from_form__mutmut_39, 
    'x__parse_provider_from_form__mutmut_40': x__parse_provider_from_form__mutmut_40, 
    'x__parse_provider_from_form__mutmut_41': x__parse_provider_from_form__mutmut_41, 
    'x__parse_provider_from_form__mutmut_42': x__parse_provider_from_form__mutmut_42, 
    'x__parse_provider_from_form__mutmut_43': x__parse_provider_from_form__mutmut_43, 
    'x__parse_provider_from_form__mutmut_44': x__parse_provider_from_form__mutmut_44, 
    'x__parse_provider_from_form__mutmut_45': x__parse_provider_from_form__mutmut_45, 
    'x__parse_provider_from_form__mutmut_46': x__parse_provider_from_form__mutmut_46, 
    'x__parse_provider_from_form__mutmut_47': x__parse_provider_from_form__mutmut_47, 
    'x__parse_provider_from_form__mutmut_48': x__parse_provider_from_form__mutmut_48, 
    'x__parse_provider_from_form__mutmut_49': x__parse_provider_from_form__mutmut_49, 
    'x__parse_provider_from_form__mutmut_50': x__parse_provider_from_form__mutmut_50, 
    'x__parse_provider_from_form__mutmut_51': x__parse_provider_from_form__mutmut_51, 
    'x__parse_provider_from_form__mutmut_52': x__parse_provider_from_form__mutmut_52, 
    'x__parse_provider_from_form__mutmut_53': x__parse_provider_from_form__mutmut_53, 
    'x__parse_provider_from_form__mutmut_54': x__parse_provider_from_form__mutmut_54, 
    'x__parse_provider_from_form__mutmut_55': x__parse_provider_from_form__mutmut_55, 
    'x__parse_provider_from_form__mutmut_56': x__parse_provider_from_form__mutmut_56, 
    'x__parse_provider_from_form__mutmut_57': x__parse_provider_from_form__mutmut_57, 
    'x__parse_provider_from_form__mutmut_58': x__parse_provider_from_form__mutmut_58, 
    'x__parse_provider_from_form__mutmut_59': x__parse_provider_from_form__mutmut_59, 
    'x__parse_provider_from_form__mutmut_60': x__parse_provider_from_form__mutmut_60, 
    'x__parse_provider_from_form__mutmut_61': x__parse_provider_from_form__mutmut_61, 
    'x__parse_provider_from_form__mutmut_62': x__parse_provider_from_form__mutmut_62, 
    'x__parse_provider_from_form__mutmut_63': x__parse_provider_from_form__mutmut_63, 
    'x__parse_provider_from_form__mutmut_64': x__parse_provider_from_form__mutmut_64, 
    'x__parse_provider_from_form__mutmut_65': x__parse_provider_from_form__mutmut_65, 
    'x__parse_provider_from_form__mutmut_66': x__parse_provider_from_form__mutmut_66, 
    'x__parse_provider_from_form__mutmut_67': x__parse_provider_from_form__mutmut_67, 
    'x__parse_provider_from_form__mutmut_68': x__parse_provider_from_form__mutmut_68, 
    'x__parse_provider_from_form__mutmut_69': x__parse_provider_from_form__mutmut_69, 
    'x__parse_provider_from_form__mutmut_70': x__parse_provider_from_form__mutmut_70, 
    'x__parse_provider_from_form__mutmut_71': x__parse_provider_from_form__mutmut_71, 
    'x__parse_provider_from_form__mutmut_72': x__parse_provider_from_form__mutmut_72, 
    'x__parse_provider_from_form__mutmut_73': x__parse_provider_from_form__mutmut_73, 
    'x__parse_provider_from_form__mutmut_74': x__parse_provider_from_form__mutmut_74, 
    'x__parse_provider_from_form__mutmut_75': x__parse_provider_from_form__mutmut_75, 
    'x__parse_provider_from_form__mutmut_76': x__parse_provider_from_form__mutmut_76, 
    'x__parse_provider_from_form__mutmut_77': x__parse_provider_from_form__mutmut_77, 
    'x__parse_provider_from_form__mutmut_78': x__parse_provider_from_form__mutmut_78, 
    'x__parse_provider_from_form__mutmut_79': x__parse_provider_from_form__mutmut_79, 
    'x__parse_provider_from_form__mutmut_80': x__parse_provider_from_form__mutmut_80, 
    'x__parse_provider_from_form__mutmut_81': x__parse_provider_from_form__mutmut_81, 
    'x__parse_provider_from_form__mutmut_82': x__parse_provider_from_form__mutmut_82, 
    'x__parse_provider_from_form__mutmut_83': x__parse_provider_from_form__mutmut_83, 
    'x__parse_provider_from_form__mutmut_84': x__parse_provider_from_form__mutmut_84, 
    'x__parse_provider_from_form__mutmut_85': x__parse_provider_from_form__mutmut_85, 
    'x__parse_provider_from_form__mutmut_86': x__parse_provider_from_form__mutmut_86, 
    'x__parse_provider_from_form__mutmut_87': x__parse_provider_from_form__mutmut_87, 
    'x__parse_provider_from_form__mutmut_88': x__parse_provider_from_form__mutmut_88, 
    'x__parse_provider_from_form__mutmut_89': x__parse_provider_from_form__mutmut_89, 
    'x__parse_provider_from_form__mutmut_90': x__parse_provider_from_form__mutmut_90, 
    'x__parse_provider_from_form__mutmut_91': x__parse_provider_from_form__mutmut_91, 
    'x__parse_provider_from_form__mutmut_92': x__parse_provider_from_form__mutmut_92, 
    'x__parse_provider_from_form__mutmut_93': x__parse_provider_from_form__mutmut_93, 
    'x__parse_provider_from_form__mutmut_94': x__parse_provider_from_form__mutmut_94, 
    'x__parse_provider_from_form__mutmut_95': x__parse_provider_from_form__mutmut_95, 
    'x__parse_provider_from_form__mutmut_96': x__parse_provider_from_form__mutmut_96, 
    'x__parse_provider_from_form__mutmut_97': x__parse_provider_from_form__mutmut_97, 
    'x__parse_provider_from_form__mutmut_98': x__parse_provider_from_form__mutmut_98, 
    'x__parse_provider_from_form__mutmut_99': x__parse_provider_from_form__mutmut_99, 
    'x__parse_provider_from_form__mutmut_100': x__parse_provider_from_form__mutmut_100, 
    'x__parse_provider_from_form__mutmut_101': x__parse_provider_from_form__mutmut_101, 
    'x__parse_provider_from_form__mutmut_102': x__parse_provider_from_form__mutmut_102, 
    'x__parse_provider_from_form__mutmut_103': x__parse_provider_from_form__mutmut_103, 
    'x__parse_provider_from_form__mutmut_104': x__parse_provider_from_form__mutmut_104, 
    'x__parse_provider_from_form__mutmut_105': x__parse_provider_from_form__mutmut_105, 
    'x__parse_provider_from_form__mutmut_106': x__parse_provider_from_form__mutmut_106, 
    'x__parse_provider_from_form__mutmut_107': x__parse_provider_from_form__mutmut_107, 
    'x__parse_provider_from_form__mutmut_108': x__parse_provider_from_form__mutmut_108, 
    'x__parse_provider_from_form__mutmut_109': x__parse_provider_from_form__mutmut_109, 
    'x__parse_provider_from_form__mutmut_110': x__parse_provider_from_form__mutmut_110, 
    'x__parse_provider_from_form__mutmut_111': x__parse_provider_from_form__mutmut_111, 
    'x__parse_provider_from_form__mutmut_112': x__parse_provider_from_form__mutmut_112, 
    'x__parse_provider_from_form__mutmut_113': x__parse_provider_from_form__mutmut_113, 
    'x__parse_provider_from_form__mutmut_114': x__parse_provider_from_form__mutmut_114, 
    'x__parse_provider_from_form__mutmut_115': x__parse_provider_from_form__mutmut_115, 
    'x__parse_provider_from_form__mutmut_116': x__parse_provider_from_form__mutmut_116, 
    'x__parse_provider_from_form__mutmut_117': x__parse_provider_from_form__mutmut_117, 
    'x__parse_provider_from_form__mutmut_118': x__parse_provider_from_form__mutmut_118, 
    'x__parse_provider_from_form__mutmut_119': x__parse_provider_from_form__mutmut_119, 
    'x__parse_provider_from_form__mutmut_120': x__parse_provider_from_form__mutmut_120, 
    'x__parse_provider_from_form__mutmut_121': x__parse_provider_from_form__mutmut_121, 
    'x__parse_provider_from_form__mutmut_122': x__parse_provider_from_form__mutmut_122, 
    'x__parse_provider_from_form__mutmut_123': x__parse_provider_from_form__mutmut_123, 
    'x__parse_provider_from_form__mutmut_124': x__parse_provider_from_form__mutmut_124, 
    'x__parse_provider_from_form__mutmut_125': x__parse_provider_from_form__mutmut_125, 
    'x__parse_provider_from_form__mutmut_126': x__parse_provider_from_form__mutmut_126, 
    'x__parse_provider_from_form__mutmut_127': x__parse_provider_from_form__mutmut_127, 
    'x__parse_provider_from_form__mutmut_128': x__parse_provider_from_form__mutmut_128, 
    'x__parse_provider_from_form__mutmut_129': x__parse_provider_from_form__mutmut_129, 
    'x__parse_provider_from_form__mutmut_130': x__parse_provider_from_form__mutmut_130, 
    'x__parse_provider_from_form__mutmut_131': x__parse_provider_from_form__mutmut_131, 
    'x__parse_provider_from_form__mutmut_132': x__parse_provider_from_form__mutmut_132, 
    'x__parse_provider_from_form__mutmut_133': x__parse_provider_from_form__mutmut_133, 
    'x__parse_provider_from_form__mutmut_134': x__parse_provider_from_form__mutmut_134, 
    'x__parse_provider_from_form__mutmut_135': x__parse_provider_from_form__mutmut_135, 
    'x__parse_provider_from_form__mutmut_136': x__parse_provider_from_form__mutmut_136, 
    'x__parse_provider_from_form__mutmut_137': x__parse_provider_from_form__mutmut_137, 
    'x__parse_provider_from_form__mutmut_138': x__parse_provider_from_form__mutmut_138, 
    'x__parse_provider_from_form__mutmut_139': x__parse_provider_from_form__mutmut_139, 
    'x__parse_provider_from_form__mutmut_140': x__parse_provider_from_form__mutmut_140, 
    'x__parse_provider_from_form__mutmut_141': x__parse_provider_from_form__mutmut_141, 
    'x__parse_provider_from_form__mutmut_142': x__parse_provider_from_form__mutmut_142, 
    'x__parse_provider_from_form__mutmut_143': x__parse_provider_from_form__mutmut_143, 
    'x__parse_provider_from_form__mutmut_144': x__parse_provider_from_form__mutmut_144, 
    'x__parse_provider_from_form__mutmut_145': x__parse_provider_from_form__mutmut_145, 
    'x__parse_provider_from_form__mutmut_146': x__parse_provider_from_form__mutmut_146, 
    'x__parse_provider_from_form__mutmut_147': x__parse_provider_from_form__mutmut_147, 
    'x__parse_provider_from_form__mutmut_148': x__parse_provider_from_form__mutmut_148
}

def _parse_provider_from_form(*args, **kwargs):
    result = _mutmut_trampoline(x__parse_provider_from_form__mutmut_orig, x__parse_provider_from_form__mutmut_mutants, args, kwargs)
    return result 

_parse_provider_from_form.__signature__ = _mutmut_signature(x__parse_provider_from_form__mutmut_orig)
x__parse_provider_from_form__mutmut_orig.__name__ = 'x__parse_provider_from_form'


def x__parse_server_settings__mutmut_orig(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_1(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = None
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_2(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get(None, '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_3(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', None).strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_4(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_5(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', ).strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_6(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('XXportXX', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_7(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('PORT', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_8(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', 'XXXX').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_9(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = None

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_10(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get(None, '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_11(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', None).strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_12(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_13(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', ).strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_14(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('XXapi_key_headerXX', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_15(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('API_KEY_HEADER', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_16(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', 'XXXX').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_17(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = None
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_18(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(None)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_19(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_20(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (2 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_21(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 < port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_22(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int < 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_23(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65536):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_24(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash(None, "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_25(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", None)
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_26(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_27(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", )
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_28(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("XXPort must be between 1 and 65535XX", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_29(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_30(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("PORT MUST BE BETWEEN 1 AND 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_31(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "XXerrorXX")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_32(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "ERROR")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_33(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header or not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_34(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_35(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(None, api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_36(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', None):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_37(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_38(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', ):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_39(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'XX^[A-Za-z0-9_-]+$XX', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_40(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[a-za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_41(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-ZA-Z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_42(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash(None, "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_43(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", None)
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_44(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_45(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", )
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_46(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("XXInvalid API key header formatXX", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_47(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("invalid api key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_48(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("INVALID API KEY HEADER FORMAT", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_49(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "XXerrorXX")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_50(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "ERROR")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_51(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'XXportXX': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_52(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'PORT': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_53(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'XXapi_key_headerXX': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_54(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'API_KEY_HEADER': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_55(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header and 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_56(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'XXX-API-KeyXX'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_57(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'x-api-key'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_58(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-KEY'
        }

    except ValueError:
        flash("Invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_59(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash(None, "error")
        return None


def x__parse_server_settings__mutmut_60(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", None)
        return None


def x__parse_server_settings__mutmut_61(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("error")
        return None


def x__parse_server_settings__mutmut_62(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", )
        return None


def x__parse_server_settings__mutmut_63(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("XXInvalid port numberXX", "error")
        return None


def x__parse_server_settings__mutmut_64(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("invalid port number", "error")
        return None


def x__parse_server_settings__mutmut_65(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("INVALID PORT NUMBER", "error")
        return None


def x__parse_server_settings__mutmut_66(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "XXerrorXX")
        return None


def x__parse_server_settings__mutmut_67(form_data) -> Optional[Dict[str, str]]:
    """Parse and validate server settings."""
    try:
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()

        if port:
            port_int = int(port)
            if not (1 <= port_int <= 65535):
                flash("Port must be between 1 and 65535", "error")
                return None

        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header format", "error")
            return None

        return {
            'port': port,
            'api_key_header': api_key_header or 'X-API-Key'
        }

    except ValueError:
        flash("Invalid port number", "ERROR")
        return None

x__parse_server_settings__mutmut_mutants : ClassVar[MutantDict] = {
'x__parse_server_settings__mutmut_1': x__parse_server_settings__mutmut_1, 
    'x__parse_server_settings__mutmut_2': x__parse_server_settings__mutmut_2, 
    'x__parse_server_settings__mutmut_3': x__parse_server_settings__mutmut_3, 
    'x__parse_server_settings__mutmut_4': x__parse_server_settings__mutmut_4, 
    'x__parse_server_settings__mutmut_5': x__parse_server_settings__mutmut_5, 
    'x__parse_server_settings__mutmut_6': x__parse_server_settings__mutmut_6, 
    'x__parse_server_settings__mutmut_7': x__parse_server_settings__mutmut_7, 
    'x__parse_server_settings__mutmut_8': x__parse_server_settings__mutmut_8, 
    'x__parse_server_settings__mutmut_9': x__parse_server_settings__mutmut_9, 
    'x__parse_server_settings__mutmut_10': x__parse_server_settings__mutmut_10, 
    'x__parse_server_settings__mutmut_11': x__parse_server_settings__mutmut_11, 
    'x__parse_server_settings__mutmut_12': x__parse_server_settings__mutmut_12, 
    'x__parse_server_settings__mutmut_13': x__parse_server_settings__mutmut_13, 
    'x__parse_server_settings__mutmut_14': x__parse_server_settings__mutmut_14, 
    'x__parse_server_settings__mutmut_15': x__parse_server_settings__mutmut_15, 
    'x__parse_server_settings__mutmut_16': x__parse_server_settings__mutmut_16, 
    'x__parse_server_settings__mutmut_17': x__parse_server_settings__mutmut_17, 
    'x__parse_server_settings__mutmut_18': x__parse_server_settings__mutmut_18, 
    'x__parse_server_settings__mutmut_19': x__parse_server_settings__mutmut_19, 
    'x__parse_server_settings__mutmut_20': x__parse_server_settings__mutmut_20, 
    'x__parse_server_settings__mutmut_21': x__parse_server_settings__mutmut_21, 
    'x__parse_server_settings__mutmut_22': x__parse_server_settings__mutmut_22, 
    'x__parse_server_settings__mutmut_23': x__parse_server_settings__mutmut_23, 
    'x__parse_server_settings__mutmut_24': x__parse_server_settings__mutmut_24, 
    'x__parse_server_settings__mutmut_25': x__parse_server_settings__mutmut_25, 
    'x__parse_server_settings__mutmut_26': x__parse_server_settings__mutmut_26, 
    'x__parse_server_settings__mutmut_27': x__parse_server_settings__mutmut_27, 
    'x__parse_server_settings__mutmut_28': x__parse_server_settings__mutmut_28, 
    'x__parse_server_settings__mutmut_29': x__parse_server_settings__mutmut_29, 
    'x__parse_server_settings__mutmut_30': x__parse_server_settings__mutmut_30, 
    'x__parse_server_settings__mutmut_31': x__parse_server_settings__mutmut_31, 
    'x__parse_server_settings__mutmut_32': x__parse_server_settings__mutmut_32, 
    'x__parse_server_settings__mutmut_33': x__parse_server_settings__mutmut_33, 
    'x__parse_server_settings__mutmut_34': x__parse_server_settings__mutmut_34, 
    'x__parse_server_settings__mutmut_35': x__parse_server_settings__mutmut_35, 
    'x__parse_server_settings__mutmut_36': x__parse_server_settings__mutmut_36, 
    'x__parse_server_settings__mutmut_37': x__parse_server_settings__mutmut_37, 
    'x__parse_server_settings__mutmut_38': x__parse_server_settings__mutmut_38, 
    'x__parse_server_settings__mutmut_39': x__parse_server_settings__mutmut_39, 
    'x__parse_server_settings__mutmut_40': x__parse_server_settings__mutmut_40, 
    'x__parse_server_settings__mutmut_41': x__parse_server_settings__mutmut_41, 
    'x__parse_server_settings__mutmut_42': x__parse_server_settings__mutmut_42, 
    'x__parse_server_settings__mutmut_43': x__parse_server_settings__mutmut_43, 
    'x__parse_server_settings__mutmut_44': x__parse_server_settings__mutmut_44, 
    'x__parse_server_settings__mutmut_45': x__parse_server_settings__mutmut_45, 
    'x__parse_server_settings__mutmut_46': x__parse_server_settings__mutmut_46, 
    'x__parse_server_settings__mutmut_47': x__parse_server_settings__mutmut_47, 
    'x__parse_server_settings__mutmut_48': x__parse_server_settings__mutmut_48, 
    'x__parse_server_settings__mutmut_49': x__parse_server_settings__mutmut_49, 
    'x__parse_server_settings__mutmut_50': x__parse_server_settings__mutmut_50, 
    'x__parse_server_settings__mutmut_51': x__parse_server_settings__mutmut_51, 
    'x__parse_server_settings__mutmut_52': x__parse_server_settings__mutmut_52, 
    'x__parse_server_settings__mutmut_53': x__parse_server_settings__mutmut_53, 
    'x__parse_server_settings__mutmut_54': x__parse_server_settings__mutmut_54, 
    'x__parse_server_settings__mutmut_55': x__parse_server_settings__mutmut_55, 
    'x__parse_server_settings__mutmut_56': x__parse_server_settings__mutmut_56, 
    'x__parse_server_settings__mutmut_57': x__parse_server_settings__mutmut_57, 
    'x__parse_server_settings__mutmut_58': x__parse_server_settings__mutmut_58, 
    'x__parse_server_settings__mutmut_59': x__parse_server_settings__mutmut_59, 
    'x__parse_server_settings__mutmut_60': x__parse_server_settings__mutmut_60, 
    'x__parse_server_settings__mutmut_61': x__parse_server_settings__mutmut_61, 
    'x__parse_server_settings__mutmut_62': x__parse_server_settings__mutmut_62, 
    'x__parse_server_settings__mutmut_63': x__parse_server_settings__mutmut_63, 
    'x__parse_server_settings__mutmut_64': x__parse_server_settings__mutmut_64, 
    'x__parse_server_settings__mutmut_65': x__parse_server_settings__mutmut_65, 
    'x__parse_server_settings__mutmut_66': x__parse_server_settings__mutmut_66, 
    'x__parse_server_settings__mutmut_67': x__parse_server_settings__mutmut_67
}

def _parse_server_settings(*args, **kwargs):
    result = _mutmut_trampoline(x__parse_server_settings__mutmut_orig, x__parse_server_settings__mutmut_mutants, args, kwargs)
    return result 

_parse_server_settings.__signature__ = _mutmut_signature(x__parse_server_settings__mutmut_orig)
x__parse_server_settings__mutmut_orig.__name__ = 'x__parse_server_settings'


def x__atomic_save_config__mutmut_orig(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_1(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = None
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_2(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix(None)
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_3(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('XX.bakXX')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_4(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.BAK')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_5(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(None, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_6(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, None)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_7(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_8(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, )

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_9(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode=None, suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_10(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix=None, delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_11(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=None) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_12(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_13(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_14(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', ) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_15(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='XXwXX', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_16(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='W', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_17(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='XX.yamlXX', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_18(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.YAML', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_19(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=True) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_20(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                None,
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_21(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                None,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_22(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=None,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_23(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=None,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_24(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=None
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_25(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_26(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_27(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_28(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_29(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_30(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'XXprovidersXX': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_31(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'PROVIDERS': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_32(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=True,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_33(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=True,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_34(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=3
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_35(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = None

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_36(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(None)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_37(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(None)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_38(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return False

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_39(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(None)
        flash("Error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_40(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash(None, "error")
        return False


def x__atomic_save_config__mutmut_41(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", None)
        return False


def x__atomic_save_config__mutmut_42(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("error")
        return False


def x__atomic_save_config__mutmut_43(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", )
        return False


def x__atomic_save_config__mutmut_44(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("XXError saving configuration fileXX", "error")
        return False


def x__atomic_save_config__mutmut_45(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("error saving configuration file", "error")
        return False


def x__atomic_save_config__mutmut_46(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("ERROR SAVING CONFIGURATION FILE", "error")
        return False


def x__atomic_save_config__mutmut_47(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "XXerrorXX")
        return False


def x__atomic_save_config__mutmut_48(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "ERROR")
        return False


def x__atomic_save_config__mutmut_49(providers: list) -> bool:
    """Atomically save configuration with backup."""
    try:
        # Create backup
        if CONFIG_PATH.exists():
            backup_path = CONFIG_PATH.with_suffix('.bak')
            shutil.copy2(CONFIG_PATH, backup_path)

        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.safe_dump(
                {'providers': providers},
                temp_file,
                default_flow_style=False,
                sort_keys=False,
                indent=2
            )
            temp_path = Path(temp_file.name)

        # Atomic move
        temp_path.replace(CONFIG_PATH)
        return True

    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash("Error saving configuration file", "error")
        return True

x__atomic_save_config__mutmut_mutants : ClassVar[MutantDict] = {
'x__atomic_save_config__mutmut_1': x__atomic_save_config__mutmut_1, 
    'x__atomic_save_config__mutmut_2': x__atomic_save_config__mutmut_2, 
    'x__atomic_save_config__mutmut_3': x__atomic_save_config__mutmut_3, 
    'x__atomic_save_config__mutmut_4': x__atomic_save_config__mutmut_4, 
    'x__atomic_save_config__mutmut_5': x__atomic_save_config__mutmut_5, 
    'x__atomic_save_config__mutmut_6': x__atomic_save_config__mutmut_6, 
    'x__atomic_save_config__mutmut_7': x__atomic_save_config__mutmut_7, 
    'x__atomic_save_config__mutmut_8': x__atomic_save_config__mutmut_8, 
    'x__atomic_save_config__mutmut_9': x__atomic_save_config__mutmut_9, 
    'x__atomic_save_config__mutmut_10': x__atomic_save_config__mutmut_10, 
    'x__atomic_save_config__mutmut_11': x__atomic_save_config__mutmut_11, 
    'x__atomic_save_config__mutmut_12': x__atomic_save_config__mutmut_12, 
    'x__atomic_save_config__mutmut_13': x__atomic_save_config__mutmut_13, 
    'x__atomic_save_config__mutmut_14': x__atomic_save_config__mutmut_14, 
    'x__atomic_save_config__mutmut_15': x__atomic_save_config__mutmut_15, 
    'x__atomic_save_config__mutmut_16': x__atomic_save_config__mutmut_16, 
    'x__atomic_save_config__mutmut_17': x__atomic_save_config__mutmut_17, 
    'x__atomic_save_config__mutmut_18': x__atomic_save_config__mutmut_18, 
    'x__atomic_save_config__mutmut_19': x__atomic_save_config__mutmut_19, 
    'x__atomic_save_config__mutmut_20': x__atomic_save_config__mutmut_20, 
    'x__atomic_save_config__mutmut_21': x__atomic_save_config__mutmut_21, 
    'x__atomic_save_config__mutmut_22': x__atomic_save_config__mutmut_22, 
    'x__atomic_save_config__mutmut_23': x__atomic_save_config__mutmut_23, 
    'x__atomic_save_config__mutmut_24': x__atomic_save_config__mutmut_24, 
    'x__atomic_save_config__mutmut_25': x__atomic_save_config__mutmut_25, 
    'x__atomic_save_config__mutmut_26': x__atomic_save_config__mutmut_26, 
    'x__atomic_save_config__mutmut_27': x__atomic_save_config__mutmut_27, 
    'x__atomic_save_config__mutmut_28': x__atomic_save_config__mutmut_28, 
    'x__atomic_save_config__mutmut_29': x__atomic_save_config__mutmut_29, 
    'x__atomic_save_config__mutmut_30': x__atomic_save_config__mutmut_30, 
    'x__atomic_save_config__mutmut_31': x__atomic_save_config__mutmut_31, 
    'x__atomic_save_config__mutmut_32': x__atomic_save_config__mutmut_32, 
    'x__atomic_save_config__mutmut_33': x__atomic_save_config__mutmut_33, 
    'x__atomic_save_config__mutmut_34': x__atomic_save_config__mutmut_34, 
    'x__atomic_save_config__mutmut_35': x__atomic_save_config__mutmut_35, 
    'x__atomic_save_config__mutmut_36': x__atomic_save_config__mutmut_36, 
    'x__atomic_save_config__mutmut_37': x__atomic_save_config__mutmut_37, 
    'x__atomic_save_config__mutmut_38': x__atomic_save_config__mutmut_38, 
    'x__atomic_save_config__mutmut_39': x__atomic_save_config__mutmut_39, 
    'x__atomic_save_config__mutmut_40': x__atomic_save_config__mutmut_40, 
    'x__atomic_save_config__mutmut_41': x__atomic_save_config__mutmut_41, 
    'x__atomic_save_config__mutmut_42': x__atomic_save_config__mutmut_42, 
    'x__atomic_save_config__mutmut_43': x__atomic_save_config__mutmut_43, 
    'x__atomic_save_config__mutmut_44': x__atomic_save_config__mutmut_44, 
    'x__atomic_save_config__mutmut_45': x__atomic_save_config__mutmut_45, 
    'x__atomic_save_config__mutmut_46': x__atomic_save_config__mutmut_46, 
    'x__atomic_save_config__mutmut_47': x__atomic_save_config__mutmut_47, 
    'x__atomic_save_config__mutmut_48': x__atomic_save_config__mutmut_48, 
    'x__atomic_save_config__mutmut_49': x__atomic_save_config__mutmut_49
}

def _atomic_save_config(*args, **kwargs):
    result = _mutmut_trampoline(x__atomic_save_config__mutmut_orig, x__atomic_save_config__mutmut_mutants, args, kwargs)
    return result 

_atomic_save_config.__signature__ = _mutmut_signature(x__atomic_save_config__mutmut_orig)
x__atomic_save_config__mutmut_orig.__name__ = 'x__atomic_save_config'


def x__atomic_save_env__mutmut_orig(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_1(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(None, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_2(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, None, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_3(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, None)

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_4(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_5(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_6(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, )

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_7(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(None))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_8(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get(None):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_9(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('XXportXX'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_10(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('PORT'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_11(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(None, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_12(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, None, server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_13(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', None)
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_14(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key('PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_15(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_16(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', )
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_17(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'XXPROXY_API_PORTXX', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_18(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'proxy_api_port', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_19(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['XXportXX'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_20(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['PORT'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_21(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get(None):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_22(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('XXapi_key_headerXX'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_23(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('API_KEY_HEADER'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_24(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(None, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_25(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, None, server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_26(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', None)

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_27(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key('PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_28(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_29(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', )

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_30(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'XXPROXY_API_API_KEY_HEADERXX', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_31(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'proxy_api_api_key_header', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_32(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['XXapi_key_headerXX'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_33(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['API_KEY_HEADER'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_34(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return False

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_35(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(None)
        flash("Error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_36(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash(None, "error")
        return False


def x__atomic_save_env__mutmut_37(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", None)
        return False


def x__atomic_save_env__mutmut_38(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("error")
        return False


def x__atomic_save_env__mutmut_39(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", )
        return False


def x__atomic_save_env__mutmut_40(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("XXError saving environment configurationXX", "error")
        return False


def x__atomic_save_env__mutmut_41(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("error saving environment configuration", "error")
        return False


def x__atomic_save_env__mutmut_42(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("ERROR SAVING ENVIRONMENT CONFIGURATION", "error")
        return False


def x__atomic_save_env__mutmut_43(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "XXerrorXX")
        return False


def x__atomic_save_env__mutmut_44(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "ERROR")
        return False


def x__atomic_save_env__mutmut_45(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update environment variables
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings
        if server_settings.get('port'):
            set_key(ENV_PATH, 'PROXY_API_PORT', server_settings['port'])
        if server_settings.get('api_key_header'):
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', server_settings['api_key_header'])

        return True

    except Exception as e:
        logger.error(f"Error saving environment: {e}")
        flash("Error saving environment configuration", "error")
        return True

x__atomic_save_env__mutmut_mutants : ClassVar[MutantDict] = {
'x__atomic_save_env__mutmut_1': x__atomic_save_env__mutmut_1, 
    'x__atomic_save_env__mutmut_2': x__atomic_save_env__mutmut_2, 
    'x__atomic_save_env__mutmut_3': x__atomic_save_env__mutmut_3, 
    'x__atomic_save_env__mutmut_4': x__atomic_save_env__mutmut_4, 
    'x__atomic_save_env__mutmut_5': x__atomic_save_env__mutmut_5, 
    'x__atomic_save_env__mutmut_6': x__atomic_save_env__mutmut_6, 
    'x__atomic_save_env__mutmut_7': x__atomic_save_env__mutmut_7, 
    'x__atomic_save_env__mutmut_8': x__atomic_save_env__mutmut_8, 
    'x__atomic_save_env__mutmut_9': x__atomic_save_env__mutmut_9, 
    'x__atomic_save_env__mutmut_10': x__atomic_save_env__mutmut_10, 
    'x__atomic_save_env__mutmut_11': x__atomic_save_env__mutmut_11, 
    'x__atomic_save_env__mutmut_12': x__atomic_save_env__mutmut_12, 
    'x__atomic_save_env__mutmut_13': x__atomic_save_env__mutmut_13, 
    'x__atomic_save_env__mutmut_14': x__atomic_save_env__mutmut_14, 
    'x__atomic_save_env__mutmut_15': x__atomic_save_env__mutmut_15, 
    'x__atomic_save_env__mutmut_16': x__atomic_save_env__mutmut_16, 
    'x__atomic_save_env__mutmut_17': x__atomic_save_env__mutmut_17, 
    'x__atomic_save_env__mutmut_18': x__atomic_save_env__mutmut_18, 
    'x__atomic_save_env__mutmut_19': x__atomic_save_env__mutmut_19, 
    'x__atomic_save_env__mutmut_20': x__atomic_save_env__mutmut_20, 
    'x__atomic_save_env__mutmut_21': x__atomic_save_env__mutmut_21, 
    'x__atomic_save_env__mutmut_22': x__atomic_save_env__mutmut_22, 
    'x__atomic_save_env__mutmut_23': x__atomic_save_env__mutmut_23, 
    'x__atomic_save_env__mutmut_24': x__atomic_save_env__mutmut_24, 
    'x__atomic_save_env__mutmut_25': x__atomic_save_env__mutmut_25, 
    'x__atomic_save_env__mutmut_26': x__atomic_save_env__mutmut_26, 
    'x__atomic_save_env__mutmut_27': x__atomic_save_env__mutmut_27, 
    'x__atomic_save_env__mutmut_28': x__atomic_save_env__mutmut_28, 
    'x__atomic_save_env__mutmut_29': x__atomic_save_env__mutmut_29, 
    'x__atomic_save_env__mutmut_30': x__atomic_save_env__mutmut_30, 
    'x__atomic_save_env__mutmut_31': x__atomic_save_env__mutmut_31, 
    'x__atomic_save_env__mutmut_32': x__atomic_save_env__mutmut_32, 
    'x__atomic_save_env__mutmut_33': x__atomic_save_env__mutmut_33, 
    'x__atomic_save_env__mutmut_34': x__atomic_save_env__mutmut_34, 
    'x__atomic_save_env__mutmut_35': x__atomic_save_env__mutmut_35, 
    'x__atomic_save_env__mutmut_36': x__atomic_save_env__mutmut_36, 
    'x__atomic_save_env__mutmut_37': x__atomic_save_env__mutmut_37, 
    'x__atomic_save_env__mutmut_38': x__atomic_save_env__mutmut_38, 
    'x__atomic_save_env__mutmut_39': x__atomic_save_env__mutmut_39, 
    'x__atomic_save_env__mutmut_40': x__atomic_save_env__mutmut_40, 
    'x__atomic_save_env__mutmut_41': x__atomic_save_env__mutmut_41, 
    'x__atomic_save_env__mutmut_42': x__atomic_save_env__mutmut_42, 
    'x__atomic_save_env__mutmut_43': x__atomic_save_env__mutmut_43, 
    'x__atomic_save_env__mutmut_44': x__atomic_save_env__mutmut_44, 
    'x__atomic_save_env__mutmut_45': x__atomic_save_env__mutmut_45
}

def _atomic_save_env(*args, **kwargs):
    result = _mutmut_trampoline(x__atomic_save_env__mutmut_orig, x__atomic_save_env__mutmut_mutants, args, kwargs)
    return result 

_atomic_save_env.__signature__ = _mutmut_signature(x__atomic_save_env__mutmut_orig)
x__atomic_save_env__mutmut_orig.__name__ = 'x__atomic_save_env'

def x_require_api_key__mutmut_orig():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_1():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint or (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_2():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') and request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_3():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith(None) or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_4():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('XXstaticXX') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_5():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('STATIC') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_6():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint not in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_7():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['XXindexXX', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_8():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['INDEX', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_9():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'XXloginXX', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_10():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'LOGIN', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_11():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'XXhealthXX', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_12():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'HEALTH', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_13():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'XXapi_discover_modelsXX', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_14():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'API_DISCOVER_MODELS', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_15():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'XXapi_validate_modelXX']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_16():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'API_VALIDATE_MODEL']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_17():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = None

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_18():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') and session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_19():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') and request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_20():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get(None) or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_21():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('XXX-API-KeyXX') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_22():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('x-api-key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_23():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-KEY') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_24():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace(None, '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_25():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', None) or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_26():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_27():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', ) or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_28():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get(None, '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_29():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', None).replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_30():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_31():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', ).replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_32():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('XXAuthorizationXX', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_33():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_34():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('AUTHORIZATION', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_35():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', 'XXXX').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_36():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('XXBearer XX', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_37():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_38():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('BEARER ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_39():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', 'XXXX') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_40():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get(None)
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_41():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('XXapi_keyXX')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_42():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('API_KEY')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_43():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_44():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning(None)
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_45():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("XXAPI key missing in requestXX")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_46():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("api key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_47():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API KEY MISSING IN REQUEST")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_48():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(None, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_49():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, None)

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_50():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort("API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_51():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, )

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_52():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(402, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_53():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "XXAPI key requiredXX")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_54():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "api key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_55():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API KEY REQUIRED")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_56():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = None
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_57():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_58():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(None):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_59():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() != api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_60():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning(None)
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_61():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("XXInvalid API key providedXX")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_62():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("invalid api key provided")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_63():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("INVALID API KEY PROVIDED")
        abort(401, "Invalid API key")

    return None

def x_require_api_key__mutmut_64():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(None, "Invalid API key")

    return None

def x_require_api_key__mutmut_65():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, None)

    return None

def x_require_api_key__mutmut_66():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort("Invalid API key")

    return None

def x_require_api_key__mutmut_67():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, )

    return None

def x_require_api_key__mutmut_68():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(402, "Invalid API key")

    return None

def x_require_api_key__mutmut_69():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "XXInvalid API keyXX")

    return None

def x_require_api_key__mutmut_70():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "invalid api key")

    return None

def x_require_api_key__mutmut_71():
    """Secure API key authentication middleware."""
    # Exempt static files and public routes
    if request.endpoint and (
        request.endpoint.startswith('static') or
        request.endpoint in ['index', 'login', 'health', 'api_discover_models', 'api_validate_model']
    ):
        return None

    # Check for API key in header or session
    api_key = (
        request.headers.get('X-API-Key') or
        request.headers.get('Authorization', '').replace('Bearer ', '') or
        session.get('api_key')
    )

    if not api_key:
        logger.warning("API key missing in request")
        abort(401, "API key required")

    # Validate API key
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys if k.strip()):
        logger.warning("Invalid API key provided")
        abort(401, "INVALID API KEY")

    return None

x_require_api_key__mutmut_mutants : ClassVar[MutantDict] = {
'x_require_api_key__mutmut_1': x_require_api_key__mutmut_1, 
    'x_require_api_key__mutmut_2': x_require_api_key__mutmut_2, 
    'x_require_api_key__mutmut_3': x_require_api_key__mutmut_3, 
    'x_require_api_key__mutmut_4': x_require_api_key__mutmut_4, 
    'x_require_api_key__mutmut_5': x_require_api_key__mutmut_5, 
    'x_require_api_key__mutmut_6': x_require_api_key__mutmut_6, 
    'x_require_api_key__mutmut_7': x_require_api_key__mutmut_7, 
    'x_require_api_key__mutmut_8': x_require_api_key__mutmut_8, 
    'x_require_api_key__mutmut_9': x_require_api_key__mutmut_9, 
    'x_require_api_key__mutmut_10': x_require_api_key__mutmut_10, 
    'x_require_api_key__mutmut_11': x_require_api_key__mutmut_11, 
    'x_require_api_key__mutmut_12': x_require_api_key__mutmut_12, 
    'x_require_api_key__mutmut_13': x_require_api_key__mutmut_13, 
    'x_require_api_key__mutmut_14': x_require_api_key__mutmut_14, 
    'x_require_api_key__mutmut_15': x_require_api_key__mutmut_15, 
    'x_require_api_key__mutmut_16': x_require_api_key__mutmut_16, 
    'x_require_api_key__mutmut_17': x_require_api_key__mutmut_17, 
    'x_require_api_key__mutmut_18': x_require_api_key__mutmut_18, 
    'x_require_api_key__mutmut_19': x_require_api_key__mutmut_19, 
    'x_require_api_key__mutmut_20': x_require_api_key__mutmut_20, 
    'x_require_api_key__mutmut_21': x_require_api_key__mutmut_21, 
    'x_require_api_key__mutmut_22': x_require_api_key__mutmut_22, 
    'x_require_api_key__mutmut_23': x_require_api_key__mutmut_23, 
    'x_require_api_key__mutmut_24': x_require_api_key__mutmut_24, 
    'x_require_api_key__mutmut_25': x_require_api_key__mutmut_25, 
    'x_require_api_key__mutmut_26': x_require_api_key__mutmut_26, 
    'x_require_api_key__mutmut_27': x_require_api_key__mutmut_27, 
    'x_require_api_key__mutmut_28': x_require_api_key__mutmut_28, 
    'x_require_api_key__mutmut_29': x_require_api_key__mutmut_29, 
    'x_require_api_key__mutmut_30': x_require_api_key__mutmut_30, 
    'x_require_api_key__mutmut_31': x_require_api_key__mutmut_31, 
    'x_require_api_key__mutmut_32': x_require_api_key__mutmut_32, 
    'x_require_api_key__mutmut_33': x_require_api_key__mutmut_33, 
    'x_require_api_key__mutmut_34': x_require_api_key__mutmut_34, 
    'x_require_api_key__mutmut_35': x_require_api_key__mutmut_35, 
    'x_require_api_key__mutmut_36': x_require_api_key__mutmut_36, 
    'x_require_api_key__mutmut_37': x_require_api_key__mutmut_37, 
    'x_require_api_key__mutmut_38': x_require_api_key__mutmut_38, 
    'x_require_api_key__mutmut_39': x_require_api_key__mutmut_39, 
    'x_require_api_key__mutmut_40': x_require_api_key__mutmut_40, 
    'x_require_api_key__mutmut_41': x_require_api_key__mutmut_41, 
    'x_require_api_key__mutmut_42': x_require_api_key__mutmut_42, 
    'x_require_api_key__mutmut_43': x_require_api_key__mutmut_43, 
    'x_require_api_key__mutmut_44': x_require_api_key__mutmut_44, 
    'x_require_api_key__mutmut_45': x_require_api_key__mutmut_45, 
    'x_require_api_key__mutmut_46': x_require_api_key__mutmut_46, 
    'x_require_api_key__mutmut_47': x_require_api_key__mutmut_47, 
    'x_require_api_key__mutmut_48': x_require_api_key__mutmut_48, 
    'x_require_api_key__mutmut_49': x_require_api_key__mutmut_49, 
    'x_require_api_key__mutmut_50': x_require_api_key__mutmut_50, 
    'x_require_api_key__mutmut_51': x_require_api_key__mutmut_51, 
    'x_require_api_key__mutmut_52': x_require_api_key__mutmut_52, 
    'x_require_api_key__mutmut_53': x_require_api_key__mutmut_53, 
    'x_require_api_key__mutmut_54': x_require_api_key__mutmut_54, 
    'x_require_api_key__mutmut_55': x_require_api_key__mutmut_55, 
    'x_require_api_key__mutmut_56': x_require_api_key__mutmut_56, 
    'x_require_api_key__mutmut_57': x_require_api_key__mutmut_57, 
    'x_require_api_key__mutmut_58': x_require_api_key__mutmut_58, 
    'x_require_api_key__mutmut_59': x_require_api_key__mutmut_59, 
    'x_require_api_key__mutmut_60': x_require_api_key__mutmut_60, 
    'x_require_api_key__mutmut_61': x_require_api_key__mutmut_61, 
    'x_require_api_key__mutmut_62': x_require_api_key__mutmut_62, 
    'x_require_api_key__mutmut_63': x_require_api_key__mutmut_63, 
    'x_require_api_key__mutmut_64': x_require_api_key__mutmut_64, 
    'x_require_api_key__mutmut_65': x_require_api_key__mutmut_65, 
    'x_require_api_key__mutmut_66': x_require_api_key__mutmut_66, 
    'x_require_api_key__mutmut_67': x_require_api_key__mutmut_67, 
    'x_require_api_key__mutmut_68': x_require_api_key__mutmut_68, 
    'x_require_api_key__mutmut_69': x_require_api_key__mutmut_69, 
    'x_require_api_key__mutmut_70': x_require_api_key__mutmut_70, 
    'x_require_api_key__mutmut_71': x_require_api_key__mutmut_71
}

def require_api_key(*args, **kwargs):
    result = _mutmut_trampoline(x_require_api_key__mutmut_orig, x_require_api_key__mutmut_mutants, args, kwargs)
    return result 

require_api_key.__signature__ = _mutmut_signature(x_require_api_key__mutmut_orig)
x_require_api_key__mutmut_orig.__name__ = 'x_require_api_key'


def x_generate_csrf_token__mutmut_orig() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_1() -> str:
    """Generate a secure CSRF token."""
    if 'XXcsrf_tokenXX' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_2() -> str:
    """Generate a secure CSRF token."""
    if 'CSRF_TOKEN' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_3() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_4() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = None
    return session['csrf_token']


def x_generate_csrf_token__mutmut_5() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['XXcsrf_tokenXX'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_6() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['CSRF_TOKEN'] = secrets.token_hex(32)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_7() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(None)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_8() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(33)
    return session['csrf_token']


def x_generate_csrf_token__mutmut_9() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['XXcsrf_tokenXX']


def x_generate_csrf_token__mutmut_10() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['CSRF_TOKEN']

x_generate_csrf_token__mutmut_mutants : ClassVar[MutantDict] = {
'x_generate_csrf_token__mutmut_1': x_generate_csrf_token__mutmut_1, 
    'x_generate_csrf_token__mutmut_2': x_generate_csrf_token__mutmut_2, 
    'x_generate_csrf_token__mutmut_3': x_generate_csrf_token__mutmut_3, 
    'x_generate_csrf_token__mutmut_4': x_generate_csrf_token__mutmut_4, 
    'x_generate_csrf_token__mutmut_5': x_generate_csrf_token__mutmut_5, 
    'x_generate_csrf_token__mutmut_6': x_generate_csrf_token__mutmut_6, 
    'x_generate_csrf_token__mutmut_7': x_generate_csrf_token__mutmut_7, 
    'x_generate_csrf_token__mutmut_8': x_generate_csrf_token__mutmut_8, 
    'x_generate_csrf_token__mutmut_9': x_generate_csrf_token__mutmut_9, 
    'x_generate_csrf_token__mutmut_10': x_generate_csrf_token__mutmut_10
}

def generate_csrf_token(*args, **kwargs):
    result = _mutmut_trampoline(x_generate_csrf_token__mutmut_orig, x_generate_csrf_token__mutmut_mutants, args, kwargs)
    return result 

generate_csrf_token.__signature__ = _mutmut_signature(x_generate_csrf_token__mutmut_orig)
x_generate_csrf_token__mutmut_orig.__name__ = 'x_generate_csrf_token'


def x_validate_csrf_token__mutmut_orig() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('csrf_token')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_1() -> bool:
    """Validate CSRF token from request."""
    token = None
    expected = session.get('csrf_token')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_2() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get(None)
    expected = session.get('csrf_token')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_3() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('XXcsrf_tokenXX')
    expected = session.get('csrf_token')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_4() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('CSRF_TOKEN')
    expected = session.get('csrf_token')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_5() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = None
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_6() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get(None)
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_7() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('XXcsrf_tokenXX')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_8() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('CSRF_TOKEN')
    return token and expected and token == expected


def x_validate_csrf_token__mutmut_9() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('csrf_token')
    return token and expected or token == expected


def x_validate_csrf_token__mutmut_10() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('csrf_token')
    return token or expected and token == expected


def x_validate_csrf_token__mutmut_11() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('csrf_token')
    return token and expected and token != expected

x_validate_csrf_token__mutmut_mutants : ClassVar[MutantDict] = {
'x_validate_csrf_token__mutmut_1': x_validate_csrf_token__mutmut_1, 
    'x_validate_csrf_token__mutmut_2': x_validate_csrf_token__mutmut_2, 
    'x_validate_csrf_token__mutmut_3': x_validate_csrf_token__mutmut_3, 
    'x_validate_csrf_token__mutmut_4': x_validate_csrf_token__mutmut_4, 
    'x_validate_csrf_token__mutmut_5': x_validate_csrf_token__mutmut_5, 
    'x_validate_csrf_token__mutmut_6': x_validate_csrf_token__mutmut_6, 
    'x_validate_csrf_token__mutmut_7': x_validate_csrf_token__mutmut_7, 
    'x_validate_csrf_token__mutmut_8': x_validate_csrf_token__mutmut_8, 
    'x_validate_csrf_token__mutmut_9': x_validate_csrf_token__mutmut_9, 
    'x_validate_csrf_token__mutmut_10': x_validate_csrf_token__mutmut_10, 
    'x_validate_csrf_token__mutmut_11': x_validate_csrf_token__mutmut_11
}

def validate_csrf_token(*args, **kwargs):
    result = _mutmut_trampoline(x_validate_csrf_token__mutmut_orig, x_validate_csrf_token__mutmut_mutants, args, kwargs)
    return result 

validate_csrf_token.__signature__ = _mutmut_signature(x_validate_csrf_token__mutmut_orig)
x_validate_csrf_token__mutmut_orig.__name__ = 'x_validate_csrf_token'


# Register authentication middleware
app.before_request(require_api_key)

# --- Routes ---

@app.route('/')
def index():
    """Main configuration page."""
    # Use pre-loaded config to avoid disk I/O on every request
    csrf_token = generate_csrf_token()
    return render_template(
        'index.html',
        config=APP_CONFIG,
        env_vars=APP_ENV_VARS,
        csrf_token=csrf_token
    )


@app.route('/save_config', methods=['POST'])
def save_config():
    """Save configuration with CSRF protection."""
    try:
        # Validate CSRF token
        if not validate_csrf_token():
            logger.warning("CSRF token validation failed")
            flash("Security validation failed. Please refresh and try again.", "error")
            return redirect(url_for('index'))

        # Save configuration
        if save_config_and_env(request.form):
            return redirect(url_for('index'))
        else:
            return redirect(url_for('index'))

    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        flash("Error saving configuration", "error")
        return redirect(url_for('index'))


@app.route('/set_key', methods=['POST'])
def set_key():
    """Set individual environment variable."""
    try:
        # Validate CSRF token
        if not validate_csrf_token():
            flash("Security validation failed", "error")
            return redirect(url_for('index'))

        env_var = request.form.get('env_var', '').strip().upper()
        value = request.form.get('value', '').strip()

        # Validation
        if not env_var or not value:
            flash("Environment variable name and value are required", "error")
            return redirect(url_for('index'))

        if not ENV_VAR_PATTERN.match(env_var) or env_var not in ALLOWED_ENV_VARS:
            flash(f"Invalid or disallowed environment variable: {env_var}", "error")
            return redirect(url_for('index'))

        # Save environment variable
        set_key(ENV_PATH, env_var, shlex.quote(value))
        logger.info(f"Environment variable {env_var} updated successfully")
        flash(f"Environment variable {env_var} set successfully", "success")

    except Exception as e:
        logger.error(f"Error setting environment variable: {e}")
        flash("Error setting environment variable", "error")

    return redirect(url_for('index'))


@app.route('/health')
def health():
    """Health check endpoint."""
    return {
        'status': 'healthy',
        'timestamp': int(time.time()),
        'service': 'web_ui'
    }

# --- Dashboard API Routes ---

@app.route('/api/dashboard/providers')
def api_dashboard_providers():
    """Get providers data for dashboard."""
    # Use pre-loaded config
    providers = APP_CONFIG.get('providers', [])

    # Add status information
    for provider in providers:
        provider['status'] = 'enabled' if provider.get('enabled', True) else 'disabled'
        provider['forced'] = provider.get('forced', False)

    return {'providers': providers}


@app.route('/api/dashboard/logs')
def api_dashboard_logs():
    """Get recent log entries for dashboard."""
    try:
        log_file = Path('logs/proxy_api.log')
        logs = list(iterate_logs(log_file, max_lines=20))
        return {'logs': logs}
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        return {'logs': [], 'error': str(e)}, 500


# --- Model Discovery API Routes ---

@app.route('/api/models/discover/<int:provider_index>')
def api_discover_models(provider_index):
    """
    (Temporarily Disabled) Discover available models for a specific provider.
    This endpoint is disabled due to performance risks from blocking asyncio calls.
    """
    logger.warning("Attempted to access disabled model discovery endpoint.")
    abort(501, "Model discovery is temporarily disabled for performance reasons.")


@app.route('/api/models/validate/<int:provider_index>/<path:model_id>')
def api_validate_model(provider_index, model_id):
    """
    (Temporarily Disabled) Validate if a specific model exists for a provider.
    This endpoint is disabled due to performance risks from blocking asyncio calls.
    """
    logger.warning("Attempted to access disabled model validation endpoint.")
    abort(501, "Model validation is temporarily disabled for performance reasons.")


# --- Error Handlers ---

@app.errorhandler(401)
def handle_unauthorized(error):
    """Handle unauthorized access."""
    flash("Authentication required", "error")
    return redirect(url_for('index'))


@app.errorhandler(500)
def handle_internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {error}")
    flash("An internal error occurred", "error")
    return redirect(url_for('index'))


# --- Main Entry Point ---

if __name__ == '__main__':
    """Run the Flask development server."""
    try:
        host = os.getenv('FLASK_HOST', '127.0.0.1')  # More secure default
        port = int(os.getenv('FLASK_PORT', '10000'))
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

        logger.info(f"Starting Flask server on {host}:{port} (debug={debug})")
        app.run(host=host, port=port, debug=debug)

    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        exit(1)
