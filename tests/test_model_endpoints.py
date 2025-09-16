"""
Comprehensive tests for model management endpoints.

This module contains tests for all model management endpoints including:
- GET /v1/providers/{provider_name}/models
- GET /v1/providers/{provider_name}/models/{model_id}
- PUT /v1/providers/{provider_name}/model_selection
- POST /v1/providers/{provider_name}/models/refresh
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime

from src.api.model_endpoints import router as model_router
from src.models.requests import ModelSelectionRequest, ModelInfoExtended
from src.models.model_info import ModelInfo
from src.core.exceptions import NotFoundError, InvalidRequestError


class TestModelEndpoints:
    """Test suite for model management endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI test application."""
        app = FastAPI()
        app.include_router(model_router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_app_state(self):
        """Mock application state."""
        return MagicMock()

    @pytest.fixture
    def mock_provider_factory(self):
        """Mock provider factory."""
        factory = AsyncMock()
        factory.get_all_provider_info = AsyncMock()
        return factory

    @pytest.fixture
    def mock_model_discovery(self):
        """Mock model discovery service."""
        discovery = AsyncMock()
        discovery.discover_models = AsyncMock()
        discovery.get_model_info = AsyncMock()
        return discovery

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        manager = MagicMock()
        manager.load_config = MagicMock()
        manager.save_config = MagicMock()
        return manager

    @pytest.fixture
    def mock_cache_manager(self):
        """Mock cache manager."""
        manager = AsyncMock()
        manager.clear_provider_cache = AsyncMock()
        return manager

    def setup_mocks(
        self,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
        mock_config_manager,
        mock_cache_manager,
    ):
        """Setup common mocks for tests."""
        app.state.app_state = mock_app_state
        mock_app_state.provider_factory = mock_provider_factory
        mock_app_state.model_discovery = mock_model_discovery
        mock_app_state.config_manager = mock_config_manager
        mock_app_state.cache_manager = mock_cache_manager

    @pytest.mark.asyncio
    async def test_list_provider_models_success(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
    ):
        """Test successful listing of models for a provider."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            MagicMock(),
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock models
        mock_models = [
            ModelInfo(id="gpt-4", created=1677649200, owned_by="openai"),
            ModelInfo(
                id="gpt-3.5-turbo", created=1677649200, owned_by="openai"
            ),
        ]
        mock_model_discovery.discover_models.return_value = mock_models

        # Make request
        response = client.get(
            "/v1/providers/openai/models",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert data["provider"] == "openai"
        assert data["total"] == 2
        assert len(data["data"]) == 2
        assert data["data"][0]["id"] == "gpt-4"
        assert data["data"][1]["id"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_list_provider_models_provider_not_found(
        self, client, app, mock_provider_factory
    ):
        """Test listing models for non-existent provider."""
        # Setup mocks
        app.state.app_state = MagicMock()
        app.state.app_state.provider_factory = mock_provider_factory
        mock_provider_factory.get_all_provider_info.return_value = []

        # Make request
        response = client.get(
            "/v1/providers/nonexistent/models",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 404
        data = response.json()
        assert "Provider 'nonexistent' not found" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_get_model_details_success(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
    ):
        """Test successful retrieval of model details."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            MagicMock(),
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "anthropic"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock model
        mock_model = ModelInfo(
            id="claude-3-opus-20240229",
            created=1709251200,
            owned_by="anthropic",
        )
        mock_model_discovery.get_model_info.return_value = mock_model

        # Make request
        response = client.get(
            "/v1/providers/anthropic/models/claude-3-opus-20240229",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "model"
        assert data["provider"] == "anthropic"
        assert data["data"]["id"] == "claude-3-opus-20240229"
        assert data["data"]["provider"] == "anthropic"

    @pytest.mark.asyncio
    async def test_get_model_details_not_found(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
    ):
        """Test getting details for non-existent model."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            MagicMock(),
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock empty models
        mock_model_discovery.discover_models.return_value = []

        # Make request
        response = client.get(
            "/v1/providers/openai/models/nonexistent-model",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 404
        data = response.json()
        assert (
            "Model 'nonexistent-model' not found" in data["error"]["message"]
        )

    @pytest.mark.asyncio
    async def test_update_model_selection_success(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
        mock_config_manager,
    ):
        """Test successful model selection update."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            mock_config_manager,
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock model
        mock_model = ModelInfo(
            id="gpt-4", created=1677649200, owned_by="openai"
        )
        mock_model_discovery.get_model_info.return_value = mock_model

        # Mock config
        mock_config = MagicMock()
        mock_config.providers = {}
        mock_config_manager.load_config.return_value = mock_config

        # Make request
        selection_data = {
            "selected_model": "gpt-4",
            "editable": True,
            "priority": 5,
            "max_tokens": 2000,
            "temperature": 0.7,
        }
        response = client.put(
            "/v1/providers/openai/model_selection",
            json=selection_data,
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "openai"
        assert data["selected_model"] == "gpt-4"
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_update_model_selection_invalid_model(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
        mock_config_manager,
    ):
        """Test updating model selection with invalid model."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            mock_config_manager,
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock empty models
        mock_model_discovery.get_model_info.return_value = None

        # Make request
        selection_data = {"selected_model": "invalid-model", "editable": True}
        response = client.put(
            "/v1/providers/openai/model_selection",
            json=selection_data,
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 404
        data = response.json()
        assert "Model 'invalid-model' not found" in data["error"]["message"]

    @pytest.mark.asyncio
    async def test_refresh_models_success(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
        mock_cache_manager,
    ):
        """Test successful model cache refresh."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            MagicMock(),
            mock_cache_manager,
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock models
        mock_models = [
            ModelInfo(id="gpt-4", created=1677649200, owned_by="openai"),
            ModelInfo(
                id="gpt-3.5-turbo", created=1677649200, owned_by="openai"
            ),
        ]
        mock_model_discovery.discover_models.return_value = mock_models
        mock_cache_manager.clear_provider_cache.return_value = True

        # Make request
        response = client.post(
            "/v1/providers/openai/models/refresh",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["provider"] == "openai"
        assert data["models_refreshed"] == 2
        assert data["cache_cleared"] is True
        assert "duration_ms" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_refresh_models_provider_not_found(
        self, client, app, mock_provider_factory
    ):
        """Test refreshing models for non-existent provider."""
        # Setup mocks
        app.state.app_state = MagicMock()
        app.state.app_state.provider_factory = mock_provider_factory
        mock_provider_factory.get_all_provider_info.return_value = []

        # Make request
        response = client.post(
            "/v1/providers/nonexistent/models/refresh",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert response
        assert response.status_code == 404
        data = response.json()
        assert "Provider 'nonexistent' not found" in data["error"]["message"]

    def test_model_selection_request_validation(self):
        """Test ModelSelectionRequest validation."""
        # Valid request
        valid_request = ModelSelectionRequest(
            selected_model="gpt-4",
            editable=True,
            priority=5,
            max_tokens=1000,
            temperature=0.8,
        )
        assert valid_request.selected_model == "gpt-4"
        assert valid_request.editable is True
        assert valid_request.priority == 5

        # Test whitespace trimming
        request_with_whitespace = ModelSelectionRequest(
            selected_model="  gpt-4  ", editable=True
        )
        assert request_with_whitespace.selected_model == "gpt-4"

        # Test invalid priority
        with pytest.raises(ValueError):
            ModelSelectionRequest(
                selected_model="gpt-4",
                editable=True,
                priority=15,  # Out of range
            )

        # Test empty model ID
        with pytest.raises(ValueError):
            ModelSelectionRequest(selected_model="   ", editable=True)

    def test_model_info_extended_creation(self):
        """Test ModelInfoExtended model creation."""
        model = ModelInfoExtended(
            id="gpt-4",
            created=1677649200,
            owned_by="openai",
            provider="openai",
            status="active",
            capabilities=["text_generation", "chat"],
            context_window=8192,
            max_tokens=4096,
            pricing={"input": 0.03, "output": 0.06},
            description="GPT-4 language model",
            version="2023-03-15",
        )

        assert model.id == "gpt-4"
        assert model.provider == "openai"
        assert "text_generation" in model.capabilities
        assert model.context_window == 8192

    @pytest.mark.asyncio
    async def test_rate_limiting(
        self,
        client,
        app,
        mock_app_state,
        mock_provider_factory,
        mock_model_discovery,
    ):
        """Test rate limiting on model endpoints."""
        # Setup mocks
        self.setup_mocks(
            app,
            mock_app_state,
            mock_provider_factory,
            mock_model_discovery,
            MagicMock(),
            MagicMock(),
        )

        # Mock provider info
        from src.core.provider_factory import ProviderStatus

        mock_provider = MagicMock()
        mock_provider.name = "openai"
        mock_provider.status = ProviderStatus.HEALTHY
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider
        ]

        # Mock models
        mock_models = [
            ModelInfo(id="gpt-4", created=1677649200, owned_by="openai")
        ]
        mock_model_discovery.discover_models.return_value = mock_models

        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(70):  # Exceed 60/minute limit
            response = client.get(
                "/v1/providers/openai/models",
                headers={"Authorization": "Bearer test-key"},
            )
            responses.append(response)

        # Should have some rate limited responses
        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0

    @pytest.mark.asyncio
    async def test_authentication_required(self, client):
        """Test that authentication is required for model endpoints."""
        endpoints = [
            "/v1/providers/openai/models",
            "/v1/providers/openai/models/gpt-4",
            "/v1/providers/openai/model_selection",
            "/v1/providers/openai/models/refresh",
        ]

        for endpoint in endpoints:
            if "model_selection" in endpoint:
                response = client.put(
                    endpoint, json={"selected_model": "test"}
                )
            elif "refresh" in endpoint:
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)

            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_error_handling(
        self, client, app, mock_app_state, mock_provider_factory
    ):
        """Test error handling for various scenarios."""
        # Setup mocks to raise exception
        app.state.app_state = mock_app_state
        mock_app_state.provider_factory = mock_provider_factory
        mock_provider_factory.get_all_provider_info.side_effect = Exception(
            "Database error"
        )

        # Make request
        response = client.get(
            "/v1/providers/openai/models",
            headers={"Authorization": "Bearer test-key"},
        )

        # Assert error response
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Database error" in data["error"]["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
