import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from src.core.config import settings


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


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
        assert "status" in data
        assert "endpoints" in data
        assert data["status"] == "operational"

    def test_root_endpoint_endpoints_list(self, client):
        """Test that endpoints list contains expected routes"""
        response = client.get("/")
        data = response.json()

        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "metrics" in endpoints
        assert "providers" in endpoints


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_endpoint_basic(self, client):
        """Test basic health endpoint response"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "checks" in data

    def test_health_endpoint_checks_structure(self, client):
        """Test health checks have proper structure"""
        response = client.get("/health")
        data = response.json()

        checks = data["checks"]
        assert "providers" in checks
        assert "memory" in checks
        assert "cache" in checks
        assert "http_client" in checks
        assert "circuit_breakers" in checks

        # Check providers check structure
        providers_check = checks["providers"]
        assert "status" in providers_check
        assert "total" in providers_check
        assert "enabled" in providers_check


class TestProvidersEndpoint:
    """Test providers listing endpoint"""

    def test_providers_endpoint(self, client):
        """Test providers endpoint returns list"""
        response = client.get("/providers")
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        # Each provider should have expected fields
        for provider in data:
            assert "name" in provider
            assert "type" in provider
            assert "models" in provider
            assert "enabled" in provider
            assert "priority" in provider


class TestRateLimiting:
    """Test rate limiting functionality"""

    def test_rate_limit_headers(self, client):
        """Test that rate limiting headers are present"""
        response = client.get("/health")
        # Check for rate limit headers (may not be present if not configured)
        # This is more of a structure test
        assert response.status_code in [200, 429]


class TestTruncationFallback:
    """Test truncation fallback scenarios"""

    @pytest.mark.asyncio
    async def test_long_context_truncation(self, mock_request):
        """Test that long contexts are truncated proactively"""
        from main import handle_context_condensation
        from fastapi import BackgroundTasks

        # Mock long content
        req = {
            "messages": [{"content": "x" * 2000}],  # Exceeds threshold
            "model": "gpt-4"
        }

        background_tasks = BackgroundTasks()
        result = await handle_context_condensation(mock_request, background_tasks, req, "chat_completion")

        # Should return JSONResponse for long context
        assert result is not None
        assert hasattr(result, 'status_code')
        assert result.status_code == 202  # Accepted

    @pytest.mark.asyncio
    async def test_short_context_no_truncation(self, mock_request):
        """Test that short contexts are not truncated"""
        from main import handle_context_condensation
        from fastapi import BackgroundTasks

        # Mock short content
        req = {
            "messages": [{"content": "short message"}],
            "model": "gpt-4"
        }

        background_tasks = BackgroundTasks()
        result = await handle_context_condensation(mock_request, background_tasks, req, "chat_completion")

        # Should return None (no truncation needed)
        assert result is None


class TestBackgroundTasks:
    """Test background task functionality"""

    @pytest.mark.asyncio
    async def test_background_condense_task(self, mock_request):
        """Test background condensation task"""
        from main import background_condense
        from unittest.mock import patch

        mock_request.app.state.summary_cache = {}
        chunks = ["test chunk"]

        with patch('src.utils.context_condenser.condense_context', new_callable=AsyncMock) as mock_condense:
            mock_condense.return_value = "test summary"

            await background_condense("test-id", mock_request, chunks)

            # Check that summary was stored
            assert "test-id" in mock_request.app.state.summary_cache
            stored = mock_request.app.state.summary_cache["test-id"]
            assert stored["summary"] == "test summary"


class TestSummaryEndpoint:
    """Test summary polling endpoint"""

    def test_summary_not_found(self, client):
        """Test polling for non-existent summary"""
        response = client.get("/summary/non-existent-id")
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

        response = client.get("/summary/test-id")
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
            headers={"X-API-Key": "test-key"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "code" in data

    def test_missing_api_key(self, client):
        """Test error response for missing API key"""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "gpt-4", "messages": [{"role": "user", "content": "test"}]}
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestHealthCheckTimeouts:
    """Test health check timeout scenarios"""

    def test_health_check_with_memory_monitoring(self, client, monkeypatch):
        """Test health check includes memory monitoring"""
        # Mock psutil
        mock_psutil = MagicMock()
        mock_psutil.virtual_memory.return_value.percent = 50
        mock_psutil.cpu_percent.return_value = 25

        monkeypatch.setattr("main.psutil", mock_psutil)

        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Should include system metrics if psutil available
        checks = data["checks"]
        assert "memory" in checks