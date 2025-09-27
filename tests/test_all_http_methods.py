import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.core.providers.factory import ProviderInfo, ProviderStatus, ProviderType

# The fixtures from conftest.py will be used.

class TestHealthEndpointHTTPMethods:
    """Test all HTTP methods for health endpoints."""

    def test_health_get_success(self, authenticated_client: TestClient):
        """Test GET /v1/health success."""
        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[]):
            with patch.object(authenticated_client.app.state.app_state.metrics_collector, 'get_all_stats', return_value={}):
                response = authenticated_client.get("/v1/health")
                assert response.status_code == 200
                json_response = response.json()
                assert "status" in json_response
                assert "providers" in json_response

    def test_health_post_method_not_allowed(self, authenticated_client: TestClient):
        """Test POST /v1/health returns 405 Method Not Allowed."""
        response = authenticated_client.post("/v1/health")
        assert response.status_code == 405


class TestChatEndpointHTTPMethods:
    """Test all HTTP methods for chat endpoints."""

    def test_chat_completions_post_success(self, authenticated_client: TestClient):
        """Test POST /v1/chat/completions success."""
        mock_response_data = {
            "id": "chatcmpl_test",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {},
        }

        mock_client = AsyncMock()
        mock_client.chat_completions = AsyncMock(return_value=mock_response_data)
        mock_config = MagicMock()
        mock_config.provider = "mock_provider"

        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_provider_client', new_callable=AsyncMock, return_value=(mock_client, mock_config)):
            data = {"model": "gpt-4", "messages": [{"role": "user", "content": "Hello"}]}
            response = authenticated_client.post("/v1/chat/completions", json=data)
            assert response.status_code == 200
            assert "choices" in response.json()

    def test_chat_completions_get_method_not_allowed(self, authenticated_client: TestClient):
        """Test GET /v1/chat/completions returns 405 Method Not Allowed."""
        response = authenticated_client.get("/v1/chat/completions")
        assert response.status_code == 405


class TestModelsEndpointHTTPMethods:
    """Test all HTTP methods for models endpoints."""

    def test_models_get_success(self, authenticated_client: TestClient):
        """Test GET /v1/models success."""
        mock_models_data = [{"id": "gpt-4", "object": "model"}]

        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'list_all_models', new_callable=AsyncMock, return_value=mock_models_data):
            response = authenticated_client.get("/v1/models")
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) > 0
            assert json_response["data"][0]['id'] == 'gpt-4'

    def test_models_post_method_not_allowed(self, authenticated_client: TestClient):
        """Test POST /v1/models returns 405 Method Not Allowed."""
        response = authenticated_client.post("/v1/models")
        assert response.status_code == 405


class TestMetricsEndpointHTTPMethods:
    """Test all HTTP methods for metrics endpoints."""

    def test_metrics_get_success(self, authenticated_client: TestClient):
        """Test GET /v1/analytics/metrics success."""
        mock_provider_info = ProviderInfo(
            name="openai", type=ProviderType.OPENAI, status=ProviderStatus.HEALTHY,
            models=["gpt-4"], priority=1, enabled=True, forced=False,
            last_health_check=time.time(), error_count=0
        )
        with patch.object(authenticated_client.app.state.app_state.metrics_collector, 'get_metrics', return_value={"openai": {"total_requests": 10}}):
             with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[mock_provider_info]):
                response = authenticated_client.get("/v1/analytics/metrics")
                assert response.status_code == 200
                assert "metrics" in response.json()

    def test_metrics_post_method_not_allowed(self, authenticated_client: TestClient):
        """Test POST /v1/analytics/metrics returns 405 Method Not Allowed."""
        response = authenticated_client.post("/v1/analytics/metrics")
        assert response.status_code == 405
