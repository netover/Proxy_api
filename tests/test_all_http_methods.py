from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

# The fixtures from conftest.py will be used.

class TestHealthEndpointHTTPMethods:
    """Test all HTTP methods for health endpoints."""

    def test_health_get_success(self, authenticated_client: TestClient):
        """Test GET /v1/health success."""
        # The endpoint relies on the real AppState, but we can mock its methods
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
        mock_provider = AsyncMock()
        mock_provider.create_completion.return_value = {
            "id": "chatcmpl_test",
            "choices": [{"message": {"content": "Test response"}}],
            "usage": {}, # Ensure usage is present
        }

        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_providers_for_model', return_value=[mock_provider]):
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
        mock_provider_info = MagicMock()
        mock_provider_info.name = "openai"
        mock_provider_info.status.value = "healthy"
        mock_provider_info.models = ["gpt-4"]

        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[mock_provider_info]):
            response = authenticated_client.get("/v1/models")
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) > 0
            assert json_response["data"][0]['id'] == 'gpt-4' # The model list should contain model names now

    def test_models_post_method_not_allowed(self, authenticated_client: TestClient):
        """Test POST /v1/models returns 405 Method Not Allowed."""
        response = authenticated_client.post("/v1/models")
        assert response.status_code == 405


class TestMetricsEndpointHTTPMethods:
    """Test all HTTP methods for metrics endpoints."""

    def test_metrics_get_success(self, authenticated_client: TestClient):
        """Test GET /v1/metrics success."""
        with patch.object(authenticated_client.app.state.app_state.metrics_collector, 'get_metrics', return_value={"openai": {"total_requests": 10}}):
             with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[]):
                response = authenticated_client.get("/v1/metrics")
                assert response.status_code == 200
                assert "metrics" in response.json()


    def test_metrics_post_method_not_allowed(self, authenticated_client: TestClient):
        """Test POST /v1/metrics returns 405 Method Not Allowed."""
        response = authenticated_client.post("/v1/metrics")
        assert response.status_code == 405
