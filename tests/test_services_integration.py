import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
import httpx
import os
from main import app
from context_service.app import app as context_app
from health_worker.app import app as health_app


@pytest.fixture
def client():
    """Main proxy test client"""
    return TestClient(app)


@pytest.fixture
def context_client():
    """Context service test client"""
    return TestClient(context_app)


@pytest.fixture
def health_client():
    """Health worker test client"""
    return TestClient(health_app)


class TestServiceIntegration:
    """Test integration between main proxy and microservices"""

    @pytest.mark.asyncio
    async def test_context_service_condensation(self, context_client):
        """Test context service condensation endpoint"""
        test_chunks = ["This is a test chunk", "Another chunk for testing"]
        response = context_client.post(
            "/condense", json={"chunks": test_chunks, "max_tokens": 100}
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert isinstance(data["summary"], str)
        assert len(data["summary"]) > 0

    @pytest.mark.asyncio
    async def test_health_worker_status(self, health_client):
        """Test health worker status endpoint"""
        response = health_client.get("/status")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "total_providers" in data
        assert "healthy_providers" in data
        assert "unhealthy_providers" in data

    @pytest.mark.asyncio
    async def test_health_worker_manual_check(self, health_client):
        """Test manual health check trigger"""
        response = health_client.post("/check")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_main_proxy_health_with_services(self, client):
        """Test main proxy health endpoint with mocked services"""
        # Mock the external service calls
        with patch("httpx.AsyncClient") as mock_client:
            # Mock context service response
            mock_context_response = AsyncMock()
            mock_context_response.status_code = 200
            mock_context_response.json.return_value = {"status": "healthy"}

            # Mock health worker response
            mock_health_response = AsyncMock()
            mock_health_response.status_code = 200
            mock_health_response.json.return_value = {
                "providers": {},
                "total_providers": 0,
                "healthy_providers": 0,
                "unhealthy_providers": 0,
            }

            # Configure mock client
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_health_response,  # First call for health worker
                mock_context_response,  # Second call for context service
            ]

            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "checks" in data
            assert "providers" in data["checks"]
            assert "context_service" in data["checks"]

    @pytest.mark.asyncio
    async def test_main_proxy_health_service_unavailable(self, client):
        """Test main proxy health when services are unavailable"""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock connection errors
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError(
                "Connection failed"
            )

            response = client.get("/health")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["checks"]["providers"]["status"] == "error"
            assert data["checks"]["context_service"]["status"] == "error"

    @pytest.mark.asyncio
    async def test_condense_context_via_service_integration(self):
        """Test the condense_context_via_service function"""
        from main import condense_context_via_service

        test_chunks = ["Test chunk 1", "Test chunk 2"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"summary": "Mocked summary"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            result = await condense_context_via_service(test_chunks, 100)

            assert result == "Mocked summary"
            mock_client.return_value.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_condense_context_via_service_error_handling(self):
        """Test error handling in condense_context_via_service"""
        from main import condense_context_via_service

        with patch("httpx.AsyncClient") as mock_client:
            # Mock HTTP error
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            with pytest.raises(
                Exception
            ):  # Should raise ServiceUnavailableError
                await condense_context_via_service(["test"], 100)

    @pytest.mark.asyncio
    async def test_background_condense_with_service(self):
        """Test background condense function with service integration"""
        from main import background_condense

        request_id = "test-123"
        mock_request = Mock()
        mock_request.app.state.summary_cache = {}

        test_chunks = ["Background test chunk"]

        with patch(
            "main.condense_context_via_service", new_callable=AsyncMock
        ) as mock_condense:
            mock_condense.return_value = "Background summary"

            await background_condense(request_id, mock_request, test_chunks)

            mock_condense.assert_called_once_with(test_chunks)
            assert request_id in mock_request.app.state.summary_cache

    @pytest.mark.asyncio
    async def test_context_service_health_endpoint(self, context_client):
        """Test context service health endpoint"""
        response = context_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "context-condensation"

    @pytest.mark.asyncio
    async def test_health_worker_health_endpoint(self, health_client):
        """Test health worker health endpoint"""
        response = health_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "health-worker"


class TestEnvironmentConfiguration:
    """Test environment variable configuration"""

    @pytest.mark.asyncio
    async def test_context_service_env_vars(self):
        """Test context service respects environment variables"""
        # Set environment variables
        original_env = os.environ.copy()

        try:
            os.environ["CACHE_SIZE"] = "500"
            os.environ["CACHE_TTL"] = "1800"
            os.environ["ADAPTIVE_ENABLED"] = "false"

            # Re-import to pick up new env vars
            import importlib
            import context_service.utils.context_condenser_impl as impl

            importlib.reload(impl)

            config = impl.get_config()
            assert config.cache_size == 500
            assert config.cache_ttl == 1800
            assert config.adaptive_enabled == False

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    @pytest.mark.asyncio
    async def test_main_proxy_env_vars(self):
        """Test main proxy respects service URLs from environment"""
        original_env = os.environ.copy()

        try:
            os.environ["CONTEXT_SERVICE_URL"] = "http://test-context:8001"
            os.environ["HEALTH_WORKER_URL"] = "http://test-health:8002"

            # The functions should use these URLs
            from main import condense_context_via_service

            with patch("httpx.AsyncClient") as mock_client:
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"summary": "test"}
                mock_response.raise_for_status.return_value = None

                mock_client.return_value.__aenter__.return_value.post.return_value = (
                    mock_response
                )

                await condense_context_via_service(["test"], 100)

                # Verify the correct URL was used
                call_args = (
                    mock_client.return_value.__aenter__.return_value.post.call_args
                )
                assert call_args[0][0] == "http://test-context:8001/condense"

        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)
