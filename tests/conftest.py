import pytest
import os
import asyncio
import yaml
from starlette.testclient import TestClient
from src.bootstrap import create_app
from src.core.config.models import UnifiedConfig
from src.core.security.auth import APIKeyAuth

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_config():
    """Loads the base test configuration from a YAML file and returns a Pydantic object."""
    config_path = os.path.join(os.path.dirname(__file__), "config.test.yaml")
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    return UnifiedConfig(**config_data)

@pytest.fixture(scope="function")
def client(test_config: UnifiedConfig, monkeypatch):
    """
    Provides a fresh, unauthenticated TestClient for each test function.
    It uses the app factory pattern and ensures that no API keys are configured.
    """
    # Explicitly set that no keys should be loaded for this client's app instance.
    test_config.proxy_api_keys = []

    app = create_app(test_config)

    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def authenticated_client(test_config: UnifiedConfig, monkeypatch):
    """
    Provides a fresh, authenticated TestClient for each test function.
    It configures the app with a specific API key.
    """
    api_key = "test-key-123"

    # Set the API key in the configuration object before creating the app.
    # This ensures the auth system is initialized correctly via the app lifespan.
    test_config.proxy_api_keys = [api_key]

    app = create_app(test_config)

    with TestClient(app) as c:
        # The API key is now managed by the app's auth system,
        # so we just need to provide it in the headers.
        c.headers["X-API-Key"] = api_key
        yield c