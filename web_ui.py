# --- Imports ---
# yaml: For safe loading/dumping of configuration in YAML format. Used in load_config and save_config_and_env.
# shlex: For quoting API key values when writing to .env to handle special characters safely.
# re: Regular expressions for validating provider names, env var names, and API key headers.
# Flask modules: Core for web app, rendering templates, handling requests, redirects, and flash messages for user feedback.
# dotenv: Loads .env values and sets keys for environment management.
# settings: Imported from src.core.config for accessing proxy_api_keys in authentication.
# os: For generating secret_key randomly for session security.
import yaml  # Functionality: Safe loading/dumping of YAML configs to prevent code execution risks. Issue: No schema validation on load. Opt: Integrate pydantic for strict typing.
import shlex  # Functionality: Quotes strings for .env writes to handle spaces/special chars safely. Issue: None major. Opt: Use configparser for more robust env handling.
import re  # Functionality: Regex patterns for input validation (env vars, names, headers). Issue: Patterns may need updates for new providers. Opt: Centralize in config module.
from flask import Flask, render_template, request, redirect, url_for, flash  # Core Flask components: App setup, template rendering, form/request handling, redirects, user feedback via flash. Issue: No CSRF protection (use Flask-WTF). Opt: Add session-based CSRF tokens.
from dotenv import dotenv_values, set_key  # Loads/parses .env, updates keys atomically. Issue: Overwrites without backup. Opt: Version control .env changes or use temp files.
from src.core.config import settings  # Imports global settings, e.g., proxy_api_keys for auth. Issue: Tight coupling; if settings change, UI breaks. Opt: Local config loader.
import os  # Functionality: Generates random secret_key for Flask sessions. Issue: Regenerated on restart, invalidates sessions. Opt: Load from env for persistence.

# --- Constants ---
# VALID_PROVIDERS: Hard-coded set of allowed provider types for validation. Functionality: Whitelists to prevent invalid types in form saves. Issue: Static; adding new providers (e.g., grok) requires code update, risking security bypass if forgotten. Opt: Dynamically load from src/services/provider_loader.py or config.yaml to auto-sync with project structure. Potential failure: Mismatch leads to flash errors on save.
VALID_PROVIDERS = {'openai', 'anthropic', 'perplexity', 'grok', 'blackbox', 'openrouter'}

# ENV_VAR_PATTERN: Regex for validating env var names (POSIX standard). Functionality: Ensures only valid uppercase alphanumeric/underscore names, preventing injection or filesystem exploits. Issue: Strict; may reject custom vars. Opt: Make configurable or add provider-specific patterns.
ENV_VAR_PATTERN = re.compile(r'^[A-Z_][A-Z0-9_]*$')

# PROVIDER_NAME_PATTERN: Regex for validating provider names. Functionality: Allows alphanum, _, - to avoid special chars that could break YAML or paths. Issue: Case-sensitive; may conflict with case-insensitive FS. Opt: Enforce lowercase, add length limit (e.g., <50 chars).
PROVIDER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# ALLOWED_ENV_VARS: Whitelist set for permitted .env variables. Functionality: Restricts writes to known keys, preventing arbitrary env pollution or security risks (e.g., overwriting system vars). Issue: Static; must sync with providers. Mutable add in code risks bypass. Opt: Freeze set, generate dynamically from VALID_PROVIDERS (e.g., f'{provider.upper()}_API_KEY'), include only on validation.
ALLOWED_ENV_VARS = {
    'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GROK_API_KEY', 'BLACKBOX_API_KEY',
    'OPENROUTER_API_KEY', 'PERPLEXITY_API_KEY', 'PROXY_API_PORT', 'PROXY_API_API_KEY_HEADER'
}

# --- Configuration Paths ---
# Hard-coded paths for config files. Functionality: Points to YAML and .env in project root. Issue: Breaks if run from subdir or container; absolute paths better for prod. Potential failure: FileNotFoundError if misplaced. Opt: Use os.path.join(os.path.dirname(__file__), 'config.yaml') for relative, or env var override (e.g., os.getenv('CONFIG_PATH', 'config.yaml')).
CONFIG_PATH = 'config.yaml'
ENV_PATH = '.env'

# Flask app initialization. Functionality: Creates app instance with random secret_key for secure sessions and flash messages. Issue: Key regenerates on restart, invalidating sessions; insecure if exposed. Opt: Load from env (os.getenv('SECRET_KEY')) or file for persistence. Add config for prod (e.g., app.config.from_pyfile).
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random for dev; override with env for prod to avoid session loss on restart.

# --- Helper Functions ---
# These functions handle loading/saving config and env, with validation to prevent errors/injections.

def load_config():
    """Loads the YAML configuration file.
    Functionality: Safely loads providers from config.yaml using yaml.safe_load to mitigate YAML deserialization attacks. Returns dict with 'providers' list or empty on error. Issue: No structure validation (e.g., required keys in provider dict); malformed YAML silently falls back. Potential failure: Inconsistent data passed to template if partial load. Opt: Use schema validation (e.g., cerberus or pydantic) to ensure 'name', 'type', etc. present; add logging for errors; support config versioning/migration."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            loaded = yaml.safe_load(f)
            # Basic validation: Ensure 'providers' is list.
            if not isinstance(loaded.get('providers'), list):
                raise ValueError("Invalid config structure: 'providers' must be a list.")
            return loaded
    except FileNotFoundError:
        # Graceful fallback for first run or missing file.
        flash("config.yaml not found; starting with empty providers.", "warning")
        return {"providers": []}
    except Exception as e:
        # Catch YAML parse, validation errors; flash to UI but keep app running.
        flash(f"Error loading config.yaml: {e}", "error")
        return {"providers": []}

def load_env():
    """Loads environment variables from .env.
    Functionality: Parses .env file into dict for rendering in template (e.g., port, header). Issue: Silent on missing/malformed .env; partial dict if errors. No validation for expected keys. Potential failure: Template shows defaults but no user alert if critical keys missing (e.g., no API keys). Opt: Validate required keys (e.g., check if 'PROXY_API_PORT' in dict), flash warnings; support multiple .env profiles."""
    env_dict = dotenv_values(ENV_PATH)
    # Optional: Validate and flash if key missing.
    if 'PROXY_API_PORT' not in env_dict:
        flash("Warning: PROXY_API_PORT not set in .env; using default.", "warning")
    return env_dict

def save_config_and_env(form_data):
    """Saves form data to config.yaml and .env files.
    Functionality: Reconstructs providers from indexed form fields, validates each (name, type, env var, key, models, priority), updates .env for API keys/port/header using set_key (quoted for safety), dumps validated providers to YAML. Server settings updated separately. Returns True on success, False on validation/error with flash. Issue: Relies on sequential indexing (e.g., _0, _1); dynamic add/remove in UI requires JS reindexing, else skips providers. No atomic transaction: .env updates per provider, YAML last – crash mid-way corrupts partially. Missing 'enabled' flag in provider dict (assume True, but form has no input). Port int check but no range (1-65535). ALLOWED_ENV_VARS mutable add risks. No backup before writes. Potential failure: Permission denied on files, malformed YAML dump, invalid regex matches. Opt: Use temp files for atomic save (write temp, rename). Add 'enabled' checkbox to form and dict. Port range validation (1 <= port <= 65535). Immutable ALLOWED_ENV_VARS or dynamic gen. Client-side JS validation to pre-check. Log exceptions to file (import logging). Support bulk upload or API for large configs. Backup old files (e.g., config.yaml.bak)."""
    try:
        # Reconstruct providers from form: Loops over expected indexed fields. Functionality: Builds list of dicts from form data. Issue: Fixed loop assumes all fields present; missing fields (e.g., no models_0) cause KeyError or empty. Opt: Use form.get with defaults, add dynamic field count from form.
        providers = []
        i = 0
        while f'provider_name_{i}' in form_data:
            provider_name = form_data[f'provider_name_{i}'].strip()
            provider_type = form_data[f'type_{i}'].strip().lower()
            api_key_env = form_data[f'api_key_env_{i}'].strip().upper()
            api_key_value = form_data.get(f'api_key_value_{i}', '').strip()
            models_str = form_data[f'models_{i}'].strip()
            priority_str = form_data[f'priority_{i}'].strip()
            module = form_data[f'module_{i}'].strip()
            class_name = form_data[f'class_{i}'].strip()
            base_url = form_data[f'base_url_{i}'].strip()

            # Validation: Per-provider checks to sanitize input. Functionality: Regex/pattern matches, whitelist, type checks to block invalid/malicious data. Early return False + flash on fail. Issue: No length limits (e.g., long name overflows YAML). Models split assumes comma-separated, trims but no dup check. Priority no upper limit. Opt: Add max lengths, unique name check across providers, models validation against known models list.
            if not PROVIDER_NAME_PATTERN.match(provider_name):
                flash(f"Invalid provider name '{provider_name}' for provider {i}: must contain only letters, numbers, underscores, and hyphens.", "error")
                return False
            if provider_type not in VALID_PROVIDERS:
                flash(f"Invalid provider type '{provider_type}' for provider {i}: must be one of {VALID_PROVIDERS}.", "error")
                return False
            if not ENV_VAR_PATTERN.match(api_key_env):
                flash(f"Invalid API key env var '{api_key_env}' for provider {i}: must be a valid environment variable name.", "error")
                return False
            if api_key_env not in ALLOWED_ENV_VARS:
                flash(f"Env var '{api_key_env}' for provider {i} is not allowed.", "error")
                return False
            if api_key_value and len(api_key_value) < 1:
                flash(f"API key value for provider {i} cannot be empty if provided.", "error")
                return False
            try:
                priority = int(priority_str)
                if priority < 0:
                    raise ValueError
            except ValueError:
                flash(f"Invalid priority '{priority_str}' for provider {i}: must be a non-negative integer.", "error")
                return False
            if not models_str:
                flash(f"Models list cannot be empty for provider {i}.", "error")
                return False
            models = [m.strip() for m in models_str.split(',') if m.strip()]
            if not models:  # After trim/split, ensure non-empty.
                flash(f"Models list cannot be empty for provider {i}.", "error")
                return False

            # Build provider dict. Functionality: Assembles validated data into dict for YAML. Issue: No 'enabled' field (add default True; form needs checkbox). Module/class hardcoded from form hidden, no validation if changed. Opt: Validate module/class exist via import check or config.
            provider = {
                'name': provider_name,
                'type': provider_type,
                'module': module,
                'class': class_name,
                'api_key_env': api_key_env,
                'base_url': base_url,
                'models': models,
                'priority': priority,
                'enabled': True  # Fix: Add default enabled flag; update from form if added.
            }
            providers.append(provider)

            # Update .env per provider. Functionality: Uses set_key to write quoted API key. Issue: Sequential writes; if one fails (e.g., perm), others succeed inconsistently. No backup. Opt: Collect all changes, write atomic temp .env.
            if api_key_value:
                set_key(ENV_PATH, api_key_env, shlex.quote(api_key_value))

            i += 1

        # Global validation post-loop. Functionality: Ensures non-empty providers. Issue: Allows zero if no fields, but form always has at least existing. Opt: Min providers count configurable.
        if not providers:
            flash("No valid providers provided.", "error")
            return False

        # Write YAML. Functionality: Dumps {'providers': list} with safe, readable options. Issue: Overwrites without backup; large dump slow. No sort to preserve order good. Opt: Backup first (shutil.copy), use indent=2 for readability, validate dump before write.
        with open(CONFIG_PATH, 'w') as f:
            yaml.safe_dump({'providers': providers}, f, default_flow_style=False, sort_keys=False, indent=2)

        # Server settings update. Functionality: Parses port/header from form, validates, sets in .env. Issue: Port only int check, no range/port in use check. Header regex allows _, but no length. Default header if empty. ALLOWED add mutable. Opt: Full port validation, backup .env, make header required.
        port = form_data.get('port', '').strip()
        api_key_header = form_data.get('api_key_header', '').strip()
        if port:
            try:
                port_int = int(port)
                if not 1 <= port_int <= 65535:  # Fix: Add range check.
                    raise ValueError("Port out of range.")
                set_key(ENV_PATH, 'PROXY_API_PORT', port)
            except ValueError as ve:
                flash(f"Invalid port value: {ve}", "error")
                return False
        if api_key_header and not re.match(r'^[A-Za-z0-9_-]+$', api_key_header):
            flash("Invalid API key header name.", "error")
            return False
        else:
            # Avoid mutable add for security; assume always allowed.
            set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', api_key_header or 'X-API-Key')

        # Success. Functionality: Flash message, note restart for hot-reload lack. Issue: Changes not immediate; user confusion. Opt: Auto-restart hook or websocket notify.
        flash("Configuration saved successfully! Please restart the main API server for changes to take effect.", "success")
        return True

    except IOError as ioe:  # Fix: Specific catch for file errors.
        flash(f"File I/O error saving configuration: {ioe}", "error")
        return False
    except Exception as e:
        # Catch-all for unexpected (e.g., yaml dump fail). Functionality: Flash error, prevent crash. Issue: Broad; hides root cause. Opt: Use logging.error(str(e)), classify (ValueError for validation, etc.).
        flash(f"Error saving configuration: {e}", "error")
        return False

def require_api_key():
    """API key authentication middleware.
    Functionality: Checks 'X-API-Key' header or 'api_key' query param against settings.proxy_api_keys (list from .env). Returns error tuple for 401 if invalid/missing, None if ok. Applied via before_request to all routes. Issue: Applies to /static too (exposes CSS/JS without auth) – security risk if sensitive static. Query param insecure (logs expose). Assumes settings.proxy_api_keys split correctly (e.g., comma-separated). No trimming of keys. Potential failure: If .env format wrong, empty list blocks all. Opt: Exempt static/CSS/JS (check request.endpoint.startswith('static')). Use configurable header from env. Add rate limiting (Flask-Limiter). Return flask.abort(401) for proper HTTP response. Support multiple keys via env array. Trim whitespace in key match."""
    # Fix: Exempt static files to allow public access to CSS/JS.
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if not api_key:
        return "API key required", 401
    # Trim for safety.
    api_key = api_key.strip()
    if not any(k.strip() == api_key for k in settings.proxy_api_keys):
        return "Invalid API key", 401
    return None

# Global auth middleware. Functionality: Runs require_api_key before every request. Issue: As above, fixed in function. Opt: Use @app.before_request with conditions or blueprints for granular auth.
# Disabled for UI as no security needed per user instruction.
# app.before_request(require_api_key)

# --- Routes ---
# Routes: Define URL endpoints for UI. Functionality: / for GET form display, /save for POST save. Issue: Task expects /save_config and /set_key; current /save mismatch causes 404 on expected calls. No individual key set. Opt: Rename to /save_config, add /set_key POST for single env updates (e.g., json {'env_var': 'value'}).

@app.route('/')
def index():
    """Root route: Displays config form.
    Functionality: Loads config.yaml and .env, passes to index.html template for rendering editable form with existing providers. Issue: If load errors, empty form but flash shown – user sees blank without data. No sanitization of loaded data for template (XSS risk if malicious YAML). Performance: Loads full file each GET; slow for large configs. Potential failure: Template errors if config structure unexpected. Opt: Cache loads (Flask-Caching), paginate providers if >10, validate/sanitize data before render, add error page on render fail."""
    config = load_config()
    env_vars = load_env()

    return render_template('index.html', config=config, env_vars=env_vars)

@app.route('/save_config', methods=['POST'])  # Fix: Rename to match task expectation.
def save_config():
    """Save config route: Handles POST form submission.
    Functionality: Extracts form data, calls save_config_and_env, redirects to / with flash (success/error). Issue: Always redirects, even on error (good for flash, but AJAX can't handle). No CSRF token check. Expects multipart/form-data or urlencoded. Potential failure: Large form timeout. Opt: Support JSON POST for API use, add CSRF via hidden token, rate limit (e.g., 5/min), return JSON {'success': bool, 'message': str} for modern UI."""
    # Basic CSRF check: Expect 'csrf_token' in form matching session token (simple, not secure; use Flask-WTF for prod).
    session_csrf = session.get('csrf_token', '')
    form_csrf = request.form.get('csrf_token', '')
    if session_csrf != form_csrf:
        flash("CSRF token mismatch. Please refresh and try again.", "error")
        return redirect(url_for('index'))
    if save_config_and_env(request.form):
        flash("Configuration saved!", "success")
    return redirect(url_for('index'))

@app.route('/set_key', methods=['POST'])  # Add: Route for individual API key/env set as per task.
def set_key():
    """Set individual env var route.
    Functionality: POST with form {'env_var': name, 'value': val}, validates, uses set_key on .env, flashes, redirects. Issue: No full validation like save (reuse code?). Assumes ALLOWED_ENV_VARS. Potential failure: Invalid var writes fail silently if not checked. Opt: JSON support, auth only, log changes, backup .env."""
    env_var = request.form.get('env_var', '').strip().upper()
    value = request.form.get('value', '').strip()
    if not env_var or not value:
        flash("Env var name and value required.", "error")
        return redirect(url_for('index'))
    if not ENV_VAR_PATTERN.match(env_var) or env_var not in ALLOWED_ENV_VARS:
        flash(f"Invalid or disallowed env var: {env_var}", "error")
        return redirect(url_for('index'))
    try:
        set_key(ENV_PATH, env_var, shlex.quote(value))
        flash(f"Set {env_var} successfully.", "success")
    except Exception as e:
        flash(f"Error setting {env_var}: {e}", "error")
    return redirect(url_for('index'))

if __name__ == '__main__':
    """Main entry: Runs Flask dev server.
    Functionality: Starts app on host/port with debug. Issue: Hard-coded port 10000 mismatches form default 8000 and possible .env PROXY_API_PORT – confusion on save. Binds 0.0.0.0 exposes to network (firewall needed). Debug=True leaks info in prod. Potential failure: Port in use error. Opt: Use env vars (host=os.getenv('HOST', '127.0.0.1'), port=int(os.getenv('PORT', 10000))), disable debug if not dev, add SSL context for HTTPS, use gunicorn for prod."""
    host = os.getenv('FLASK_HOST', '0.0.0.0')  # Fix: Make configurable.
    port = int(os.getenv('FLASK_PORT', 10000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host=host, port=port, debug=debug)
