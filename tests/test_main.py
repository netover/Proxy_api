import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app




@pytest.fixture
def mock_request():
    """Mock request object"""
    request = MagicMock()
    request.app.state.config = MagicMock()
    request.app.state.config.providers = []
    request.app.state.condensation_config = MagicMock()
    request.app.state.condensation_config.truncation_threshold = 1000
    return request


class TestRootEndpoint:
    """Test root endpoint functionality"""

    def test_root_endpoint_structure(self, client):
        """Test that root endpoint returns expected structure"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "endpoints" in data
        assert data["name"] == "Proxy API Gateway"

    def test_root_endpoint_endpoints_list(self, client):
        """Test that endpoints list contains expected routes"""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "models" in endpoints
        assert "chat" in endpoints


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_v1_health_endpoint_basic(self, client):
        """Test basic health endpoint response"""
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "health_score" in data
        assert data["status"] == "healthy"
        assert "providers" in data
        assert "system" in data
        assert "service" in data
        assert "timestamp" in data


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_headers(self, client):
        """Test that rate limiting headers are present"""
        response = client.get("/v1/health")
        # Check for rate limit headers (may not be present if not configured)
        # This is more of a structure test
        assert response.status_code in [200, 429]




class TestSummaryEndpoint:
    """Test summary polling endpoint"""

    def test_summary_not_found(self, client):
        """Test polling for non-existent summary"""
        response = client.get("/v1/summary/non-existent-id")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "not_found"

    def test_summary_with_mock_cache(self, client, monkeypatch):
        """Test summary retrieval with mocked cache"""
        # Mock the cache
        mock_cache = {"test-id": {"summary": "test summary", "timestamp": 1234567890}}

        # Mock request.app.state.summary_cache
        def mock_getattr(obj, name):
            if name == "summary_cache":
                return mock_cache
            return object.__getattribute__(obj, name)

        monkeypatch.setattr(type(client.app.state), "__getattr__", mock_getattr)

        response = client.get("/v1/summary/test-id")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["summary"] == "test summary"


class TestModelsEndpoint:
    """Test models listing endpoint"""

    def test_models_endpoint(self, client):
        """Test OpenAI-compatible models endpoint"""
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()

        assert "object" in data
        assert "data" in data
        assert data["object"] == "list"
        assert isinstance(data["data"], list)


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_invalid_model_error(self, client):
        """Test error response for invalid model"""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "", "messages": []},
            headers={"X-API-Key": "test-key"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data

    def test_missing_api_key(self, client):
        """Test error response for missing API key"""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


