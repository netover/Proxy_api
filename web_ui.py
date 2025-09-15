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

def get_persistent_secret_key() -> str:
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

def load_config_once() -> Dict[str, Any]:
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

def load_env_once() -> Dict[str, str]:
    """Load .env file once, intended for app startup."""
    return dotenv_values(ENV_PATH)

# Load configurations at startup to avoid repeated disk I/O
APP_CONFIG = load_config_once()
APP_ENV_VARS = load_env_once()

def save_config_and_env(form_data: Dict[str, Any]) -> bool:
    """Save configuration and environment variables atomically."""
    try:
        # 1. Parse all settings into a structured dictionary
        full_config = _parse_global_settings_from_form(form_data)

        providers = []
        env_updates = {}
        i = 0
        while f'provider_name_{i}' in form_data:
            provider_data = _parse_provider_from_form(form_data, i)
            if not provider_data:
                return False  # Parsing failed, flash message already sent
            providers.append(provider_data)
            if provider_data.get('api_key_value'):
                env_updates[provider_data['api_key_env']] = provider_data['api_key_value']
            i += 1

        if not providers:
            flash("At least one provider is required.", "error")
            return False

        # Construct the final configuration object, flattening the settings
        final_config = full_config.get('settings', {})
        final_config['providers'] = providers

        # 2. Save the complete config to config.yaml
        if not _atomic_save_config(final_config):
            return False

        # 3. Save environment-specific variables to .env
        if not _atomic_save_env(form_data, env_updates):
            return False

        flash("Configuration saved successfully! Restart the API server for changes to take effect.", "success")
        logger.info("Configuration saved successfully.")
        return True

    except Exception as e:
        logger.error(f"Error saving configuration: {e}", exc_info=True)
        flash(f"An unexpected error occurred while saving: {e}", "error")
        return False


def _parse_provider_from_form(form_data, index: int) -> Optional[Dict[str, Any]]:
    """Parse and validate a single provider from form data."""
    def get_form_value(key, default, cast_to=str):
        val = form_data.get(key, '').strip()
        if not val:
            return default
        try:
            return cast_to(val)
        except (ValueError, TypeError):
            flash(f"Invalid value for {key}: {val}", "error")
            return None

    try:
        provider_name = get_form_value(f'provider_name_{index}', None)
        if not provider_name or not PROVIDER_NAME_PATTERN.match(provider_name):
            flash(f"Invalid provider name: {provider_name}", "error")
            return None

        provider_type = get_form_value(f'type_{index}', '').lower()
        if provider_type not in VALID_PROVIDERS:
            flash(f"Invalid provider type: {provider_type}", "error")
            return None

        api_key_env = get_form_value(f'api_key_env_{index}', '').upper()
        if not api_key_env or not ENV_VAR_PATTERN.match(api_key_env):
            flash(f"Invalid environment variable name: {api_key_env}", "error")
            return None

        models_str = get_form_value(f'models_{index}', '')
        models = [m.strip() for m in models_str.split(',') if m.strip()]
        if not models:
            flash(f"No valid models specified for provider {provider_name}", "error")
            return None

        custom_headers_str = form_data.get(f'custom_headers_{index}', '{}').strip()
        try:
            custom_headers = json.loads(custom_headers_str)
            if not isinstance(custom_headers, dict):
                raise ValueError("Custom headers must be a JSON object.")
        except json.JSONDecodeError:
            flash(f"Invalid JSON for custom headers in provider {provider_name}", "error")
            return None

        return {
            'name': provider_name,
            'type': provider_type,
            'api_key_env': api_key_env,
            'api_key_value': get_form_value(f'api_key_value_{index}', ''),
            'base_url': get_form_value(f'base_url_{index}', ''),
            'models': models,
            'enabled': form_data.get(f'enabled_{index}') == 'true',
            'forced': form_data.get(f'forced_{index}') == 'true',
            'priority': get_form_value(f'priority_{index}', 100, int),
            'timeout': get_form_value(f'timeout_{index}', 30, int),
            'max_retries': get_form_value(f'max_retries_{index}', 3, int),
            'retry_delay': get_form_value(f'retry_delay_{index}', 1.0, float),
            'rate_limit': get_form_value(f'rate_limit_{index}', None, int),
            'max_connections': get_form_value(f'max_connections_{index}', 1000, int),
            'max_keepalive_connections': get_form_value(f'max_keepalive_connections_{index}', 100, int),
            'keepalive_expiry': get_form_value(f'keepalive_expiry_{index}', 30.0, float),
            'custom_headers': custom_headers,
        }

    except Exception as e:
        logger.error(f"Error parsing provider {index}: {e}", exc_info=True)
        flash(f"An error occurred while parsing provider {index}.", "error")
        return None


def _parse_global_settings_from_form(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Parses all global, cache, and condensation settings from the form."""

    def get_form_value(key, default, cast_to=str, is_bool=False):
        if is_bool:
            return form_data.get(key) == 'true'

        val = form_data.get(key, '').strip()
        if not val:
            return default
        try:
            return cast_to(val)
        except (ValueError, TypeError):
            return default

    def get_list(key, default=None):
        default = default or []
        val = form_data.get(key, '').strip()
        return [item.strip() for item in val.split(',') if item.strip()] or default

    settings = {
        "api_keys": [key.strip() for key in form_data.get('api_keys', '').split('\n') if key.strip()],
        "cors_origins": [origin.strip() for origin in form_data.get('cors_origins', '').split('\n') if origin.strip()],
        "rate_limit_rpm": get_form_value('rate_limit_rpm', 1000, int),
        "rate_limit_window": get_form_value('rate_limit_window', 60, int),
        "circuit_breaker_threshold": get_form_value('circuit_breaker_threshold', 5, int),
        "circuit_breaker_timeout": get_form_value('circuit_breaker_timeout', 60, int),
        "cache": {
            "cache_enabled": get_form_value('cache_enabled', True, is_bool=True),
            "cache_ttl": get_form_value('cache_ttl', 300, int),
            "cache_persist": get_form_value('cache_persist', False, is_bool=True),
            "cache_dir": get_form_value('cache_dir', None),
        },
        "condensation": {
            "cache_ttl": get_form_value('condensation_cache_ttl', 3600, int),
            "cache_size": get_form_value('condensation_cache_size', 1000, int),
            "truncation_threshold": get_form_value('truncation_threshold', 2000, int),
            "max_tokens_default": get_form_value('max_tokens_default', 512, int),
            "adaptive_factor": get_form_value('adaptive_factor', 0.5, float),
            "error_keywords": get_list('error_keywords', ["context_length_exceeded", "token_limit"]),
            "fallback_strategies": get_list('fallback_strategies', ["truncate", "secondary_provider"]),
            "cache_persist": get_form_value('condensation_cache_persist', False, is_bool=True),
            "adaptive_enabled": get_form_value('adaptive_enabled', True, is_bool=True),
            "dynamic_reload": get_form_value('dynamic_reload', True, is_bool=True),
        }
    }
    return {"settings": settings}


def _atomic_save_config(config_data: Dict[str, Any]) -> bool:
    """Atomically save the entire configuration object with backup."""
    try:
        if CONFIG_PATH.exists():
            shutil.copy2(CONFIG_PATH, CONFIG_PATH.with_suffix('.bak'))

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, dir=CONFIG_PATH.parent) as temp_file:
            yaml.safe_dump(config_data, temp_file, default_flow_style=False, sort_keys=False, indent=2)
            temp_path = Path(temp_file.name)

        temp_path.replace(CONFIG_PATH)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}", exc_info=True)
        flash("Error saving configuration file.", "error")
        return False


def _atomic_save_env(form_data: Dict[str, Any], env_updates: Dict[str, str]) -> bool:
    """Atomically save environment variables."""
    try:
        # Update provider API keys
        for key, value in env_updates.items():
            if value:  # Only set non-empty values
                set_key(ENV_PATH, key, shlex.quote(value))

        # Update server settings from the main form
        port = form_data.get('port', '').strip()
        if port:
            set_key(ENV_PATH, 'PROXY_API_PORT', port)

        api_key_header = form_data.get('api_key_header', '').strip()
        if api_key_header:
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', api_key_header)

        return True
    except Exception as e:
        logger.error(f"Error saving environment variables: {e}", exc_info=True)
        flash("Error saving environment configuration.", "error")
        return False

def require_api_key():
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


def generate_csrf_token() -> str:
    """Generate a secure CSRF token."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


def validate_csrf_token() -> bool:
    """Validate CSRF token from request."""
    token = request.form.get('csrf_token')
    expected = session.get('csrf_token')
    return token and expected and token == expected


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
