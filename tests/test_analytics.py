import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app  # Assuming the FastAPI app is defined in main.py

client = TestClient(app)


@pytest.mark.asyncio
async def test_get_metrics_success():
    """Test get metrics endpoint success."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector:

        # Mock metrics data
        mock_stats = {
            "openai": {
                "total_requests": 100,
                "success_rate": 0.95,
                "average_response_time": 1.2,
                "error_count": 5,
            },
            "anthropic": {
                "total_requests": 50,
                "success_rate": 0.98,
                "average_response_time": 2.1,
                "error_count": 1,
            },
        }
        mock_metrics_collector.get_all_stats.return_value = mock_stats

        # Mock provider info
        mock_provider1 = Mock()
        mock_provider1.name = "openai"
        mock_provider1.status.value = "healthy"
        mock_provider1.models = ["gpt-3.5-turbo", "gpt-4"]
        mock_provider1.priority = 1
        mock_provider1.enabled = True
        mock_provider1.forced = False
        mock_provider1.last_health_check = time.time()
        mock_provider1.error_count = 5

        mock_provider2 = Mock()
        mock_provider2.name = "anthropic"
        mock_provider2.status.value = "healthy"
        mock_provider2.models = ["claude-3-sonnet"]
        mock_provider2.priority = 2
        mock_provider2.enabled = True
        mock_provider2.forced = False
        mock_provider2.last_health_check = time.time()
        mock_provider2.error_count = 1

        mock_provider_factory = AsyncMock()
        mock_provider_factory.get_all_provider_info.return_value = [
            mock_provider1,
            mock_provider2,
        ]

        # Mock the app state in the request
        mock_app_state = Mock()
        mock_app_state.provider_factory = mock_provider_factory

        with patch.object(app.state, "app_state", mock_app_state):
            async with AsyncClient(app=app, base_url="http://test") as ac:
                headers = {"Authorization": "Bearer test_key"}
                response = await ac.get("/metrics", headers=headers)
                assert response.status_code == 200
                json_response = response.json()

                assert "timestamp" in json_response
                assert "providers" in json_response
                assert "summary" in json_response

                # Check providers data
                assert "openai" in json_response["providers"]
                assert "anthropic" in json_response["providers"]

                openai_data = json_response["providers"]["openai"]
                assert openai_data["status"] == "healthy"
                assert openai_data["models"] == ["gpt-3.5-turbo", "gpt-4"]
                assert openai_data["priority"] == 1
                assert openai_data["enabled"] is True
                assert openai_data["forced"] is False
                assert "last_health_check" in openai_data
                assert openai_data["error_count"] == 5

                # Check summary
                summary = json_response["summary"]
                assert summary["total_providers"] == 2
                assert summary["total_requests"] == 150  # 100 + 50
                assert summary["average_success_rate"] == 0.965  # (0.95 + 0.98) / 2


@pytest.mark.asyncio
async def test_get_metrics_no_api_key():
    """Test get metrics endpoint without API key."""
    async with AsyncClient(base_url="http://test") as ac:
        response = await ac.get("http://test/metrics")
        assert response.status_code == 401
        json_response = response.json()
        assert "detail" in json_response
        assert "API key required" in json_response["detail"]


@pytest.mark.asyncio
async def test_get_metrics_invalid_api_key():
    """Test get metrics endpoint with invalid API key."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": "Bearer invalid_key"}
        response = await ac.get("/metrics", headers=headers)
        assert response.status_code == 401
        json_response = response.json()
        assert "detail" in json_response
        assert "Invalid or unauthorized API key" in json_response["detail"]


@pytest.mark.asyncio
async def test_get_metrics_empty_providers():
    """Test get metrics endpoint with no providers."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector, patch(
        "src.api.controllers.analytics_controller.app_state"
    ) as mock_app_state:

        mock_metrics_collector.get_all_stats.return_value = {}

        mock_provider_factory = AsyncMock()
        mock_provider_factory.get_all_provider_info.return_value = []
        mock_app_state.provider_factory = mock_provider_factory

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics", headers=headers)
            assert response.status_code == 200
            json_response = response.json()

            assert json_response["providers"] == {}
            assert json_response["summary"]["total_providers"] == 0
            assert json_response["summary"]["total_requests"] == 0
            assert json_response["summary"]["average_success_rate"] == 0.0


@pytest.mark.asyncio
async def test_get_prometheus_metrics_success():
    """Test get prometheus metrics endpoint success."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector:
        prometheus_data = """# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/metrics"} 150
# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_bucket{le="0.1"} 10
response_time_seconds_bucket{le="1.0"} 140
response_time_seconds_bucket{le="10.0"} 150
response_time_seconds_bucket{le="+Inf"} 150
response_time_seconds_sum 225.5
response_time_seconds_count 150
"""

        mock_metrics_collector.get_prometheus_metrics.return_value = prometheus_data

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics/prometheus", headers=headers)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            assert prometheus_data in response.text


@pytest.mark.asyncio
async def test_get_prometheus_metrics_no_api_key():
    """Test get prometheus metrics endpoint without API key."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/metrics/prometheus")
        assert response.status_code == 401
        json_response = response.json()
        assert "detail" in json_response
        assert "API key required" in json_response["detail"]


@pytest.mark.asyncio
async def test_get_prometheus_metrics_invalid_api_key():
    """Test get prometheus metrics endpoint with invalid API key."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        headers = {"Authorization": "Bearer invalid_key"}
        response = await ac.get("/metrics/prometheus", headers=headers)
        assert response.status_code == 401
        json_response = response.json()
        assert "detail" in json_response
        assert "Invalid or unauthorized API key" in json_response["detail"]


@pytest.mark.asyncio
async def test_get_prometheus_metrics_empty():
    """Test get prometheus metrics endpoint with empty data."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector:
        mock_metrics_collector.get_prometheus_metrics.return_value = None

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics/prometheus", headers=headers)
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"
            assert response.text == ""


@pytest.mark.asyncio
async def test_metrics_with_provider_errors():
    """Test metrics endpoint with providers having errors."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector, patch(
        "src.api.controllers.analytics_controller.app_state"
    ) as mock_app_state:

        mock_stats = {
            "openai": {
                "total_requests": 100,
                "success_rate": 0.8,
                "error_count": 20,
            }
        }
        mock_metrics_collector.get_all_stats.return_value = mock_stats

        mock_provider = Mock()
        mock_provider.name = "openai"
        mock_provider.status.value = "degraded"
        mock_provider.models = ["gpt-3.5-turbo"]
        mock_provider.priority = 1
        mock_provider.enabled = True
        mock_provider.forced = False
        mock_provider.last_health_check = time.time() - 3600  # 1 hour ago
        mock_provider.error_count = 20

        mock_provider_factory = AsyncMock()
        mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
        mock_app_state.provider_factory = mock_provider_factory

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics", headers=headers)
            assert response.status_code == 200
            json_response = response.json()

            openai_data = json_response["providers"]["openai"]
            assert openai_data["status"] == "degraded"
            assert openai_data["error_count"] == 20
            assert "last_health_check" in openai_data


@pytest.mark.asyncio
async def test_metrics_with_forced_provider():
    """Test metrics endpoint with a forced provider."""
    with patch(
        "src.api.controllers.analytics_controller.metrics_collector"
    ) as mock_metrics_collector, patch(
        "src.api.controllers.analytics_controller.app_state"
    ) as mock_app_state:

        mock_stats = {"openai": {"total_requests": 200, "success_rate": 0.9}}
        mock_metrics_collector.get_all_stats.return_value = mock_stats

        mock_provider = Mock()
        mock_provider.name = "openai"
        mock_provider.status.value = "healthy"
        mock_provider.models = ["gpt-3.5-turbo"]
        mock_provider.priority = 1
        mock_provider.enabled = True
        mock_provider.forced = True  # This provider is forced
        mock_provider.last_health_check = time.time()
        mock_provider.error_count = 0

        mock_provider_factory = AsyncMock()
        mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
        mock_app_state.provider_factory = mock_provider_factory

        async with AsyncClient(app=app, base_url="http://test") as ac:
            headers = {"Authorization": "Bearer test_key"}
            response = await ac.get("/metrics", headers=headers)
            assert response.status_code == 200
            json_response = response.json()

            openai_data = json_response["providers"]["openai"]
            assert openai_data["forced"] is True
