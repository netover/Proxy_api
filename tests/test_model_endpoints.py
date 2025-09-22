import pytest
from unittest.mock import AsyncMock, patch, ANY
from fastapi.testclient import TestClient
from fastapi import HTTPException

from src.models.requests import ModelListResponse, ModelInfoExtended, ModelDetailResponse, RefreshResponse
from src.core.exceptions import NotFoundError
from src.api.model_endpoints import model_manager

# The client fixture is from conftest.py

@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_list_provider_models_success(mock_manager: AsyncMock, client: TestClient):
    """Test successful listing of models for a provider."""
    mock_return = ModelListResponse(
        object="list",
        data=[ModelInfoExtended(id="gpt-4", created=123, owned_by="openai", provider="openai", status="active", capabilities=[])],
        provider="openai",
        total=1,
        cached=False,
        last_refresh=12345
    )
    mock_manager.get_provider_models.return_value = mock_return

    response = client.get("/v1/providers/openai/models", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 1
    assert data["data"][0]["id"] == "gpt-4"
    mock_manager.get_provider_models.assert_awaited_once_with(ANY, "openai")


@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_list_provider_models_not_found(mock_manager: AsyncMock, client: TestClient):
    """Test listing models for a non-existent provider."""
    # Simulate the exception handler's behavior by raising HTTPException
    mock_manager.get_provider_models.side_effect = HTTPException(status_code=404, detail="Provider not found")

    response = client.get("/v1/providers/nonexistent/models", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 404
    assert "Provider not found" in response.json()["detail"]
    mock_manager.get_provider_models.assert_awaited_once()


@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_get_model_details_success(mock_manager: AsyncMock, client: TestClient):
    """Test successful retrieval of model details."""
    mock_return = ModelDetailResponse(
        object="model",
        data=ModelInfoExtended(id="gpt-4", created=123, owned_by="openai", provider="openai", status="active", capabilities=[]),
        provider="openai",
        cached=True,
        last_refresh=12345
    )
    mock_manager.get_model_details.return_value = mock_return

    response = client.get("/v1/providers/openai/models/gpt-4", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "model"
    assert data["data"]["id"] == "gpt-4"
    mock_manager.get_model_details.assert_awaited_once()


@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_update_model_selection_success(mock_manager: AsyncMock, client: TestClient):
    """Test successful model selection update."""
    mock_manager.update_model_selection.return_value = {"success": True}
    selection_data = {
        "selected_model": "gpt-4",
        "editable": True,
        "priority": 10,
        "max_tokens": 4096,
        "temperature": 0.7
    }

    response = client.put("/v1/providers/openai/model_selection", json=selection_data, headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_manager.update_model_selection.assert_awaited_once()

@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_refresh_models_success(mock_manager: AsyncMock, client: TestClient):
    """Test successful model cache refresh."""
    mock_manager.refresh_models.return_value = RefreshResponse(success=True, models_refreshed=10, provider="openai", cache_cleared=True, duration_ms=100.0, timestamp=12345)

    response = client.post("/v1/providers/openai/models/refresh", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["models_refreshed"] == 10
    mock_manager.refresh_models.assert_awaited_once()


@pytest.mark.asyncio
@patch('src.api.model_endpoints.model_manager', new_callable=AsyncMock)
async def test_get_model_details_raises_not_found(mock_manager: AsyncMock, client: TestClient):
    """Test that getting a non-existent model raises NotFoundError."""
    # Simulate the exception handler's behavior by raising HTTPException
    mock_manager.get_model_details.side_effect = HTTPException(status_code=404, detail="Model not found")

    response = client.get("/v1/providers/openai/models/not-a-model", headers={"Authorization": "Bearer test-key"})

    assert response.status_code == 404
    assert "Model not found" in response.json()["detail"]
    mock_manager.get_model_details.assert_awaited_once()
