import pytest
import os
from starlette.testclient import TestClient
from src.core.unified_config import config_manager
from src.bootstrap import app as fastapi_app
from unittest.mock import patch

# Keep the event loop session-scoped as it's safe
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def client(monkeypatch):
    """
    Provides a completely fresh TestClient for each test, with its own app instance
    and a clean, initialized state. Lifespan is managed per-test.
    API keys are unset by default.
    """
    monkeypatch.delenv("PROXY_API_KEYS", raising=False)

    # Reset the singleton config to ensure a clean slate for each test
    config_manager.reset()
    config_path = os.path.join(os.path.dirname(__file__), "config.test.yaml")
    config_manager.load_config(config_path)

    # The TestClient context manager handles the lifespan of the app
    with TestClient(fastapi_app) as c:
        yield c

@pytest.fixture(scope="function")
def authenticated_client(monkeypatch):
    """
    Provides a fresh, authenticated TestClient for each test.
    A default API key is set in the environment, and the client is configured
    with the corresponding auth header.
    """
    api_key = "test-key"
    monkeypatch.setenv("PROXY_API_KEYS", api_key)

    # Reset config and load test config
    config_manager.reset()
    config_path = os.path.join(os.path.dirname(__file__), "config.test.yaml")
    config_manager.load_config(config_path)

    with TestClient(fastapi_app) as c:
        c.headers = {"X-API-Key": api_key}
        yield c
