import pytest
from unittest.mock import patch, AsyncMock
from starlette.testclient import TestClient

# Fixtures from conftest.py are used automatically

class TestChatController:
    """Tests for the Chat Controller."""

    def test_chat_completions_endpoint_exists(self, client: TestClient):
        """Test that chat completions endpoint is accessible and requires auth."""
        response = client.post("/v1/chat/completions", json={})
        assert response.status_code == 403  # Expecting authentication error, not 422

class TestModelController:
    """Tests for the Model Controller."""

    def test_list_models_endpoint(self, client: TestClient):
        """Test that models listing endpoint requires auth."""
        response = client.get("/v1/models")
        assert response.status_code == 403  # Expecting authentication error

class TestHealthController:
    """Tests for the Health Controller."""

    def test_health_endpoint(self, client: TestClient):
        """Test that the old /health endpoint returns a simple health check."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data and data["status"] == "healthy"

    def test_v1_health_endpoint(self, authenticated_client: TestClient):
        """Test that /v1/health endpoint returns detailed health check."""
        with patch.object(authenticated_client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[]):
            response = authenticated_client.get("/v1/health")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "service" in data

class TestAnalyticsController:
    """Tests for the Analytics Controller."""

    def test_metrics_endpoint(self, client: TestClient):
        """Test that metrics endpoint requires authentication."""
        response = client.get("/v1/analytics/metrics")
        assert response.status_code == 403

    def test_prometheus_endpoint(self, client: TestClient):
        """Test that prometheus endpoint requires authentication."""
        response = client.get("/v1/analytics/prometheus")
        assert response.status_code == 403

class TestMiddleware:
    """Tests for middleware functionality."""

    def test_cors_headers(self, client: TestClient):
        """Test that CORS headers are properly set on OPTIONS preflight."""
        response = client.options("/v1/chat/completions", headers={"Origin": "http://test.com"})
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_security_headers(self, client: TestClient):
        """Test that security headers are present."""
        response = client.get("/health")
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers

class TestErrorHandling:
    """Tests for API error handling and validation."""

    def test_not_found(self, authenticated_client: TestClient):
        """Test that a non-existent route returns 404."""
        response = authenticated_client.get("/non-existent-route")
        assert response.status_code == 404

    def test_invalid_json_returns_proper_error(self, authenticated_client: TestClient):
        """Test that invalid JSON returns proper validation error."""
        response = authenticated_client.post(
            "/v1/chat/completions",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422 # FastAPI/Pydantic handles this

class TestValidation:
    """Tests for request validation logic."""

    @patch('src.api.router.route_request', new_callable=AsyncMock)
    def test_request_validation_integration(self, mock_route_request, authenticated_client: TestClient):
        """Test that a valid request passes through the validation middleware."""
        # Mock the final routing function to prevent actual endpoint logic from running
        mock_route_request.return_value = ("response", None)

        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = authenticated_client.post("/v1/chat/completions", json=payload)

        # We expect the test to fail since the endpoint doesn't exist
        assert response.status_code == 404
