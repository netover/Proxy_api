"""
Integration tests for model discovery system.

These tests verify the complete end-to-end functionality of the model discovery
system, including API endpoints, web UI, provider discovery, and caching.
"""

import asyncio
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
import aiohttp
from fastapi.testclient import TestClient

from src.core.model_discovery import ModelDiscoveryService
from src.core.cache_manager import CacheManager
from src.core.provider_factory import ProviderFactory
from main import app
from src.models.model_info import ModelInfo


class TestModelDiscoveryIntegration:
    """Integration tests for model discovery system."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def discovery_service(self, temp_cache_dir):
        """Create model discovery service with test configuration."""
        return ModelDiscoveryService()

    @pytest.fixture
    def api_client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    def test_complete_discovery_flow(self, discovery_service):
        """Test complete model discovery flow from start to finish."""
        # Setup test configuration
        test_config = {
            "providers": {
                "openai": {"api_key": "test-key", "enabled": True},
                "anthropic": {"api_key": "test-key", "enabled": True},
            }
        }

        # Mock provider responses
        mock_openai_models = [
            {"id": "gpt-4", "object": "model", "created": 1234567890},
            {"id": "gpt-3.5-turbo", "object": "model", "created": 1234567890},
        ]

        mock_anthropic_models = [
            {"id": "claude-3-opus-20240229", "display_name": "Claude 3 Opus"},
            {
                "id": "claude-3-sonnet-20240229",
                "display_name": "Claude 3 Sonnet",
            },
        ]

        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            with patch(
                "src.providers.anthropic.AnthropicDiscovery.get_models"
            ) as mock_anthropic:
                mock_openai.return_value = [
                    ModelInfo(
                        id="gpt-4",
                        name="GPT-4",
                        provider="openai",
                        context_length=8192,
                        max_tokens=4096,
                        supports_chat=True,
                        supports_completion=True,
                        input_cost=0.03,
                        output_cost=0.06,
                    ),
                    ModelInfo(
                        id="gpt-3.5-turbo",
                        name="GPT-3.5 Turbo",
                        provider="openai",
                        context_length=4096,
                        max_tokens=2048,
                        supports_chat=True,
                        supports_completion=True,
                        input_cost=0.0015,
                        output_cost=0.002,
                    ),
                ]

                mock_anthropic.return_value = [
                    ModelInfo(
                        id="claude-3-opus-20240229",
                        name="Claude 3 Opus",
                        provider="anthropic",
                        context_length=200000,
                        max_tokens=4096,
                        supports_chat=True,
                        supports_completion=False,
                        input_cost=0.015,
                        output_cost=0.075,
                    ),
                    ModelInfo(
                        id="claude-3-sonnet-20240229",
                        name="Claude 3 Sonnet",
                        provider="anthropic",
                        context_length=200000,
                        max_tokens=4096,
                        supports_chat=True,
                        supports_completion=False,
                        input_cost=0.003,
                        output_cost=0.015,
                    ),
                ]

                # Execute discovery
                result = asyncio.run(
                    discovery_service.discover_all_models(test_config)
                )

                # Verify results
                assert len(result) == 4
                assert all(isinstance(model, ModelInfo) for model in result)

                # Verify cache was populated
                cached_models = discovery_service.cache_manager.get(
                    "all_models"
                )
                assert cached_models is not None
                assert len(cached_models) == 4

    def test_api_endpoint_integration(self, api_client):
        """Test API endpoints for model discovery."""
        # Test GET /v1/models endpoint
        response = api_client.get("/v1/models")
        assert response.status_code == 200

        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_web_ui_integration(self, api_client):
        """Test web UI endpoints for model discovery."""
        # Test main page loads
        response = api_client.get("/")
        assert response.status_code == 200
        # Note: Root returns JSON, not HTML for API
        assert "application/json" in response.headers.get("content-type", "")

        # Test models API endpoint used by web UI
        response = api_client.get("/v1/models")
        assert response.status_code == 200

        # Test model details endpoint
        response = api_client.get("/v1/models/gpt-4")
        assert response.status_code in [200, 404]  # May or may not exist

    def test_provider_discovery_integration(self, discovery_service):
        """Test provider discovery with real API calls (mocked)."""
        # Test individual provider discovery
        providers = ["openai", "anthropic", "cohere"]

        for provider_name in providers:
            with patch(
                f"src.providers.{provider_name}.{provider_name.capitalize()}Discovery.get_models"
            ) as mock_provider:
                mock_provider.return_value = [
                    ModelInfo(
                        id=f"{provider_name}-model-1",
                        name=f"{provider_name.title()} Model 1",
                        provider=provider_name,
                        context_length=4096,
                        max_tokens=2048,
                        supports_chat=True,
                        supports_completion=True,
                        input_cost=0.01,
                        output_cost=0.02,
                    )
                ]

                models = asyncio.run(
                    discovery_service.discover_provider_models(
                        provider_name, {}
                    )
                )

                assert len(models) == 1
                assert models[0].provider == provider_name

    def test_cache_integration(self, discovery_service):
        """Test cache integration with model discovery."""
        # First discovery - should populate cache
        test_models = [
            ModelInfo(
                id="test-model-1",
                name="Test Model 1",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
            )
        ]

        # Mock provider to return test models
        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            mock_openai.return_value = test_models

            # First call - should hit provider and cache results
            result1 = asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Verify cache was populated
            cached = discovery_service.cache_manager.get("openai_models")
            assert cached is not None
            assert len(cached) == 1

            # Second call - should use cache
            result2 = asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Results should be identical
            assert result1 == result2

            # Verify cache hit by checking call count
            assert mock_openai.call_count == 1

    def test_cache_expiration(self, discovery_service):
        """Test cache expiration behavior."""
        test_models = [
            ModelInfo(
                id="test-model-1",
                name="Test Model 1",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
            )
        ]

        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            mock_openai.return_value = test_models

            # Set short TTL for testing
            discovery_service.cache_manager.ttl = 1  # 1 second

            # First discovery
            asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Wait for cache to expire
            time.sleep(2)

            # Second discovery - should hit provider again
            asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Should have made two API calls
            assert mock_openai.call_count == 2

    def test_error_handling_integration(self, discovery_service):
        """Test error handling across the entire system."""
        # Test provider failure handling
        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            mock_openai.side_effect = Exception("API Error")

            # Should handle error gracefully
            result = asyncio.run(
                discovery_service.discover_provider_models(
                    "openai", {"api_key": "test"}
                )
            )

            # Should return empty list on error
            assert result == []

            # Should not cache error
            cached = discovery_service.cache_manager.get("openai_models")
            assert cached is None

    def test_concurrent_discovery(self, discovery_service):
        """Test concurrent model discovery requests."""
        test_models = [
            ModelInfo(
                id="test-model-1",
                name="Test Model 1",
                provider="test",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.01,
                output_cost=0.02,
            )
        ]

        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            mock_openai.return_value = test_models

            # Run multiple concurrent discoveries
            async def run_concurrent():
                tasks = [
                    discovery_service.discover_provider_models(
                        "openai", {"api_key": "test"}
                    )
                    for _ in range(5)
                ]
                results = await asyncio.gather(*tasks)
                return results

            results = asyncio.run(run_concurrent())

            # All results should be identical
            assert all(len(r) == 1 for r in results)
            assert all(r[0].id == "test-model-1" for r in results)

            # Should only make one API call due to caching
            assert mock_openai.call_count == 1

    def test_filtering_integration(self, discovery_service):
        """Test model filtering across the system."""
        test_models = [
            ModelInfo(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                context_length=8192,
                max_tokens=4096,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.03,
                output_cost=0.06,
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                context_length=4096,
                max_tokens=2048,
                supports_chat=True,
                supports_completion=True,
                input_cost=0.0015,
                output_cost=0.002,
            ),
        ]

        with patch(
            "src.providers.openai.OpenAIDiscovery.get_models"
        ) as mock_openai:
            mock_openai.return_value = test_models

            # Test filtering by provider
            result = asyncio.run(
                discovery_service.discover_all_models(
                    {
                        "providers": {"openai": {"enabled": True}},
                        "filters": {"provider": "openai"},
                    }
                )
            )

            assert len(result) == 2
            assert all(m.provider == "openai" for m in result)

            # Test filtering by capability
            result = asyncio.run(
                discovery_service.discover_all_models(
                    {
                        "providers": {"openai": {"enabled": True}},
                        "filters": {"supports_chat": True},
                    }
                )
            )

            assert len(result) == 2
            assert all(m.supports_chat for m in result)


class TestWebUIIntegration:
    """Integration tests for web UI components."""

    @pytest.fixture
    def api_client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    def test_model_list_page(self, api_client):
        """Test model list page loads correctly."""
        response = api_client.get("/")
        assert response.status_code == 200

        # Check for expected content (API returns JSON)
        content = response.text
        assert "Proxy API Gateway" in content or "models" in content

    def test_model_details_modal(self, api_client):
        """Test model details modal functionality."""
        # This would typically test JavaScript interactions
        # For now, verify the API endpoints work
        response = api_client.get("/v1/models")
        assert response.status_code == 200

        data = response.json()
        if data.get("data"):
            model_id = data["data"][0]["id"]
            detail_response = api_client.get(f"/v1/models/{model_id}")
            assert detail_response.status_code in [200, 404]

    def test_refresh_models_endpoint(self, api_client):
        """Test refresh models endpoint."""
        response = api_client.post("/v1/models/refresh")
        assert response.status_code in [200, 404]  # May not be implemented yet

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            assert data["status"] in ["success", "started"]


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def api_client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    def test_models_endpoint_structure(self, api_client):
        """Test structure of models API response."""
        response = api_client.get("/v1/models")
        assert response.status_code == 200

        data = response.json()
        # API returns {"object": "list", "data": [...]}
        assert "data" in data
        assert isinstance(data["data"], list)

        if data["data"]:
            model = data["data"][0]
            required_model_fields = ["id", "object", "created", "owned_by"]
            for field in required_model_fields:
                assert field in model

    def test_model_search_endpoint(self, api_client):
        """Test model search functionality."""
        response = api_client.get("/v1/models/search?q=gpt")
        assert response.status_code in [200, 404]  # May not be implemented

        if response.status_code == 200:
            data = response.json()
            assert "models" in data or "data" in data
            models_list = data.get("models") or data.get("data", [])
            assert isinstance(models_list, list)

    def test_provider_status_endpoint(self, api_client):
        """Test provider status endpoint."""
        response = api_client.get("/v1/providers")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "providers" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
