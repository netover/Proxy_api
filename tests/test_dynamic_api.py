import pytest
import time
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from main_dynamic import app as main_app
from src.core.auth import verify_api_key
from src.providers.dynamic_base import DynamicProvider

@pytest.fixture
def mock_provider():
    """Creates a default mock provider instance for testing."""
    provider = AsyncMock(spec=DynamicProvider)
    provider.name = "mock_provider"
    provider.models = ["test-model"]
    provider.priority = 1
    provider.create_completion.return_value = {
        "id": "chatcmpl-mock-id",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "test-model",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Mocked response"}, "finish_reason": "stop"}],
    }
    # Mock the async context manager methods for graceful shutdown
    provider.client = AsyncMock()
    provider.client.aclose.return_value = None
    return provider

@pytest.fixture
def client(mock_provider):
    """
    This is the primary test fixture. It uses unittest.mock.patch to replace
    the provider loading function before the app starts up. This ensures the
    lifespan event uses the mocked function.
    """
    with patch("main_dynamic.instantiate_providers") as mock_loader:
        # Configure the mock that replaces the function
        mock_loader.return_value = [mock_provider]

        # Override auth dependency
        main_app.dependency_overrides[verify_api_key] = lambda: True

        # Now, when TestClient starts the app, the lifespan manager will call
        # the mocked version of instantiate_providers
        with TestClient(main_app) as c:
            yield c

    # Cleanup is handled automatically by the patch context manager
    # and we just need to clear the auth override
    main_app.dependency_overrides = {}

# --- Tests ---

def test_health_check_endpoint(client):
    """Test the health check endpoint uses the mocked provider count."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["providers"] == 1

def test_providers_endpoint(client, mock_provider):
    """Test that the /providers endpoint shows the mocked provider."""
    response = client.get("/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == mock_provider.name

def test_chat_completions_success(client, mock_provider):
    """Test a successful chat completion call."""
    request_data = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "chatcmpl-mock-id"
    mock_provider.create_completion.assert_called_once_with(request_data)

def test_chat_completions_unsupported_model(client):
    """Test a request for a model not supported by the mock provider."""
    request_data = {
        "model": "unsupported-model",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 400
    assert "not supported by any provider" in response.json()["detail"]

def test_chat_completions_provider_failure(client, mock_provider):
    """Test when the provider fails by raising an exception."""
    mock_provider.create_completion.side_effect = Exception("Provider API is down")
    request_data = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = client.post("/v1/chat/completions", json=request_data)
    assert response.status_code == 503
    assert "All providers are currently unavailable" in response.json()["detail"]
