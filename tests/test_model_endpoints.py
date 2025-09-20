"""
Refactored tests for model management endpoints.
This version uses centralized fixtures to reduce boilerplate.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.model_endpoints import router as model_router
from src.models.model_info import ModelInfo

# A single app instance and client for all tests in this module
@pytest.fixture(scope="module")
def app():
    app = FastAPI()
    app.include_router(model_router)
    return app

@pytest.fixture(scope="module")
def client(app):
    with TestClient(app) as c:
        yield c

# This master fixture sets up all mocks and injects them into the app state.
# It runs automatically for every test in this module.
@pytest.fixture(autouse=True)
def mock_dependencies(app):
    # Create mock objects for all dependencies
    mock_app_state = MagicMock()
    mock_provider_factory = AsyncMock()
    mock_model_discovery = AsyncMock()
    mock_config_manager = MagicMock()
    mock_cache_manager = AsyncMock()

    # Set up the relationships between mocks
    mock_app_state.provider_factory = mock_provider_factory
    mock_app_state.model_discovery = mock_model_discovery
    mock_app_state.config_manager = mock_config_manager
    mock_app_state.cache_manager = mock_cache_manager

    # Patch the app's state for all requests
    app.state.app_state = mock_app_state

    # Yield the mocks in a dictionary so tests can access them
    mocks = {
        "provider_factory": mock_provider_factory,
        "model_discovery": mock_model_discovery,
        "config_manager": mock_config_manager,
        "cache_manager": mock_cache_manager,
    }
    yield mocks

# Helper to create a mock provider
def create_mock_provider(name="openai"):
    from src.core.provider_factory import ProviderStatus
    mock_provider = MagicMock()
    mock_provider.name = name
    mock_provider.status = ProviderStatus.HEALTHY
    return mock_provider

# --- Test Cases ---

@pytest.mark.asyncio
async def test_list_provider_models_success(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("openai")]
    mock_models = [
        ModelInfo(id="gpt-4", created=1677649200, owned_by="openai"),
        ModelInfo(id="gpt-3.5-turbo", created=1677649200, owned_by="openai"),
    ]
    mock_dependencies["model_discovery"].discover_models.return_value = mock_models

    # Act
    response = client.get("/v1/providers/openai/models", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai"
    assert len(data["data"]) == 2

@pytest.mark.asyncio
async def test_list_provider_models_provider_not_found(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = []

    # Act
    response = client.get("/v1/providers/nonexistent/models", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_model_details_success(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("anthropic")]
    mock_model = ModelInfo(id="claude-3-opus", created=1709251200, owned_by="anthropic")
    mock_dependencies["model_discovery"].get_model_info.return_value = mock_model

    # Act
    response = client.get("/v1/providers/anthropic/models/claude-3-opus", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == "claude-3-opus"

@pytest.mark.asyncio
async def test_get_model_details_not_found(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("openai")]
    mock_dependencies["model_discovery"].get_model_info.return_value = None # Simulate model not found

    # Act
    response = client.get("/v1/providers/openai/models/nonexistent-model", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_model_selection_success(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("openai")]
    mock_dependencies["model_discovery"].get_model_info.return_value = ModelInfo(id="gpt-4", created=1, owned_by="openai")
    mock_dependencies["config_manager"].load_config.return_value = MagicMock()

    selection_data = {"selected_model": "gpt-4", "editable": True}

    # Act
    response = client.put("/v1/providers/openai/model_selection", json=selection_data, headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    mock_dependencies["config_manager"].save_config.assert_called_once()

@pytest.mark.asyncio
async def test_update_model_selection_invalid_model(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("openai")]
    mock_dependencies["model_discovery"].get_model_info.return_value = None

    selection_data = {"selected_model": "invalid-model", "editable": True}

    # Act
    response = client.put("/v1/providers/openai/model_selection", json=selection_data, headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_refresh_models_success(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = [create_mock_provider("openai")]
    mock_models = [ModelInfo(id="gpt-4", created=1, owned_by="openai")]
    mock_dependencies["model_discovery"].discover_models.return_value = mock_models

    # Act
    response = client.post("/v1/providers/openai/models/refresh", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["models_refreshed"] == 1
    mock_dependencies["cache_manager"].clear_provider_cache.assert_called_once_with("openai")

@pytest.mark.asyncio
async def test_refresh_models_provider_not_found(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.return_value = []

    # Act
    response = client.post("/v1/providers/nonexistent/models/refresh", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_authentication_required(client):
    # This test does not need mocks as it should fail before they are called.
    endpoints = {
        "GET": ["/v1/providers/openai/models", "/v1/providers/openai/models/gpt-4"],
        "POST": ["/v1/providers/openai/models/refresh"],
        "PUT": ["/v1/providers/openai/model_selection"],
    }

    for method, paths in endpoints.items():
        for path in paths:
            if method == "GET":
                response = client.get(path)
            elif method == "POST":
                response = client.post(path)
            elif method == "PUT":
                response = client.put(path, json={"selected_model": "test"})

            assert response.status_code == 403, f"Failed for {method} {path}"

@pytest.mark.asyncio
async def test_error_handling(client, mock_dependencies):
    # Arrange
    mock_dependencies["provider_factory"].get_all_provider_info.side_effect = Exception("Database error")

    # Act
    response = client.get("/v1/providers/openai/models", headers={"Authorization": "Bearer test-key"})

    # Assert
    assert response.status_code == 500  # Should be 500 for unhandled exceptions
    assert "Database error" in response.json()["detail"]
