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

# Initialize Flask app with security
app = Flask(__name__)

# Security configuration
app.config.update(
    SECRET_KEY=os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
    WTF_CSRF_ENABLED=True,
    WTF_CSRF_TIME_LIMIT=3600
)

# Initialize logger
logger = ContextualLogger(__name__)

# --- Helper Functions ---

def load_config() -> Dict[str, Any]:
    """Load configuration with validation and error handling."""
    try:
        if not CONFIG_PATH.exists():
            logger.warning("Configuration file not found, using defaults")
            return {"providers": []}

        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}

        # Validate structure
        if not isinstance(config.get('providers', []), list):
            raise ValueError("Invalid config: 'providers' must be a list")

        # Validate each provider
        for provider in config.get('providers', []):
            if not isinstance(provider, dict):
                raise ValueError("Invalid provider format")
            required_keys = ['name', 'type', 'models']
            for key in required_keys:
                if key not in provider:
                    raise ValueError(f"Provider missing required key: {key}")

        return config

    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        flash("Configuration file contains invalid YAML syntax", "error")
        return {"providers": []}
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        flash(f"Error loading configuration: {str(e)}", "error")
        return {"providers": []}

def load_env() -> Dict[str, str]:
    """Load environment variables with validation."""
    try:
        env_dict = dotenv_values(ENV_PATH)

        # Validate critical environment variables
        critical_vars = ['PROXY_API_PORT']
        for var in critical_vars:
            if var not in env_dict or not env_dict[var]:
                logger.warning(f"Critical environment variable missing: {var}")
                flash(f"Warning: {var} not set in .env", "warning")

        return env_dict

    except Exception as e:
        logger.error(f"Error loading environment file: {e}")
        flash("Error loading environment configuration", "error")
        return {}

def save_config_and_env(form_data) -> bool:
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


def _parse_provider_from_form(form_data, index: int) -> Optional[Dict[str, Any]]:
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


def _parse_server_settings(form_data) -> Optional[Dict[str, str]]:
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


def _atomic_save_config(providers: list) -> bool:
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


def _atomic_save_env(env_updates: Dict[str, str], server_settings: Dict[str, str]) -> bool:
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
    try:
        config = load_config()
        env_vars = load_env()
        csrf_token = generate_csrf_token()

        return render_template(
            'index.html',
            config=config,
            env_vars=env_vars,
            csrf_token=csrf_token
        )
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        flash("Error loading configuration", "error")
        return render_template('index.html', config={'providers': []}, env_vars={}, csrf_token=generate_csrf_token())


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
    try:
        config = load_config()
        providers = config.get('providers', [])

        # Add status information
        for provider in providers:
            provider['status'] = 'enabled' if provider.get('enabled', True) else 'disabled'
            provider['forced'] = provider.get('forced', False)

        return {'providers': providers}
    except Exception as e:
        logger.error(f"Error fetching providers: {e}")
        return {'providers': [], 'error': str(e)}, 500


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
    """Discover available models for a specific provider."""
    try:
        config = load_config()
        providers = config.get('providers', [])
        
        if provider_index >= len(providers):
            return {'models': [], 'error': 'Provider index out of range'}, 400
        
        provider = providers[provider_index]
        env_vars = load_env()
        
        # Get API key from environment
        api_key_env = provider.get('api_key_env', '')
        api_key = env_vars.get(api_key_env, '')
        
        if not api_key:
            return {'models': [], 'error': f'API key not found for {api_key_env}'}, 400
        
        # Create provider config
        provider_config = ProviderConfig(
            name=provider['name'],
            base_url=provider.get('base_url', 'https://api.openai.com'),
            api_key=api_key
        )
        
        # Discover models
        import asyncio
        async def discover():
            service = ModelDiscoveryService()
            try:
                models = await service.discover_models(provider_config)
                return [model.to_dict() for model in models]
            finally:
                await service.close()
        
        models = asyncio.run(discover())
        
        return {
            'models': models,
            'provider_name': provider['name'],
            'provider_type': provider['type'],
            'count': len(models)
        }
        
    except Exception as e:
        logger.error(f"Error discovering models: {e}")
        return {'models': [], 'error': str(e)}, 500


@app.route('/api/models/validate/<int:provider_index>/<path:model_id>')
def api_validate_model(provider_index, model_id):
    """Validate if a specific model exists for a provider."""
    try:
        config = load_config()
        providers = config.get('providers', [])
        
        if provider_index >= len(providers):
            return {'valid': False, 'error': 'Provider index out of range'}, 400
        
        provider = providers[provider_index]
        env_vars = load_env()
        
        # Get API key from environment
        api_key_env = provider.get('api_key_env', '')
        api_key = env_vars.get(api_key_env, '')
        
        if not api_key:
            return {'valid': False, 'error': f'API key not found for {api_key_env}'}, 400
        
        # Create provider config
        provider_config = ProviderConfig(
            name=provider['name'],
            base_url=provider.get('base_url', 'https://api.openai.com'),
            api_key=api_key
        )
        
        # Validate model
        import asyncio
        async def validate():
            service = ModelDiscoveryService()
            try:
                is_valid = await service.validate_model(provider_config, model_id)
                return is_valid
            finally:
                await service.close()
        
        is_valid = asyncio.run(validate())
        
        return {
            'valid': is_valid,
            'model_id': model_id,
            'provider_name': provider['name']
        }
        
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        return {'valid': False, 'error': str(e)}, 500


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
