import yaml
from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import dotenv_values, set_key
import os

# --- Configuration Paths ---
# Assuming web_ui.py is in the root directory alongside config.yaml
CONFIG_PATH = 'config.yaml'
ENV_PATH = '.env'

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for flashing messages

# --- Helper Functions ---

def load_config():
    """Loads the YAML configuration file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {"providers": []}
    except Exception as e:
        flash(f"Error loading config.yaml: {e}", "error")
        return {"providers": []}

def load_env():
    """Loads the .env file."""
    return dotenv_values(ENV_PATH)

def save_config_and_env(form_data):
    """Saves the configuration to YAML and .env files."""
    try:
        # Reconstruct providers list from form data
        providers = []
        i = 0
        while f'provider_name_{i}' in form_data:
            provider = {
                'name': form_data[f'provider_name_{i}'],
                'type': form_data[f'type_{i}'],
                'module': form_data[f'module_{i}'],
                'class': form_data[f'class_{i}'],
                'api_key_env': form_data[f'api_key_env_{i}'],
                'base_url': form_data[f'base_url_{i}'],
                'models': [m.strip() for m in form_data[f'models_{i}'].split(',')],
                'priority': int(form_data[f'priority_{i}'])
            }
            providers.append(provider)

            # Update the .env file with the new API key value
            api_key_value = form_data.get(f'api_key_value_{i}')
            if api_key_value:
                set_key(ENV_PATH, provider['api_key_env'], api_key_value)

            i += 1

        # Write back to config.yaml
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump({'providers': providers}, f, default_flow_style=False, sort_keys=False)

        # Update other .env variables
        set_key(ENV_PATH, 'PROXY_API_PORT', form_data.get('port'))
        set_key(ENV_PATH, 'PROXY_API_API_KEY_HEADER', form_data.get('api_key_header'))

        flash("Configuration saved successfully! Please restart the main API server for changes to take effect.", "success")
        return True

    except Exception as e:
        flash(f"Error saving configuration: {e}", "error")
        return False

# --- Routes ---

@app.route('/')
def index():
    """Displays the configuration form."""
    config = load_config()
    env_vars = load_env()

    # Combine env vars into the provider configs for easier templating
    for provider in config.get('providers', []):
        api_key_env = provider.get('api_key_env')
        if api_key_env:
            provider['api_key_value'] = env_vars.get(api_key_env, '')

    return render_template('index.html', config=config, env_vars=env_vars)

@app.route('/save', methods=['POST'])
def save():
    """Saves the configuration from the form."""
    save_config_and_env(request.form)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
