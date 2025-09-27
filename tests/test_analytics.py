import pytest
import time
from unittest.mock import patch, AsyncMock
from starlette.testclient import TestClient
from src.core.providers.factory import ProviderInfo, ProviderStatus, ProviderType

# Fixtures `client` and `authenticated_client` are used from conftest.

def test_get_metrics_success(authenticated_client: TestClient):
    """Test get metrics endpoint success."""
    client = authenticated_client

    # Mock data
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

    mock_provider1 = ProviderInfo(
        name="openai",
        type=ProviderType.OPENAI,
        status=ProviderStatus.HEALTHY,
        models=["gpt-3.5-turbo", "gpt-4"],
        priority=1,
        enabled=True,
        forced=False,
        last_health_check=time.time(),
        error_count=5
    )

    mock_provider2 = ProviderInfo(
        name="anthropic",
        type=ProviderType.ANTHROPIC,
        status=ProviderStatus.HEALTHY,
        models=["claude-3-sonnet"],
        priority=2,
        enabled=True,
        forced=False,
        last_health_check=time.time(),
        error_count=1
    )

    with patch.object(client.app.state.app_state.metrics_collector, 'get_metrics', return_value=mock_stats), \
         patch.object(client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[mock_provider1, mock_provider2]):

        response = client.get("/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
        assert "provider_details" in data
        assert "openai" in data["metrics"]
        assert "anthropic" in data["metrics"]
        assert len(data["provider_details"]) == 2

def test_get_metrics_no_api_key(client: TestClient):
    """Test get metrics endpoint without API key returns 403."""
    response = client.get("/v1/analytics/metrics")
    assert response.status_code == 403
    assert "Not authenticated" in response.json()['detail']

def test_get_metrics_invalid_api_key(client: TestClient):
    """Test get metrics endpoint with invalid API key returns 401."""
    headers = {"X-API-Key": "invalid_key"}
    response = client.get("/v1/analytics/metrics", headers=headers)
    assert response.status_code == 401
    assert "Invalid API Key" in response.json()['detail']

def test_get_metrics_empty_providers(authenticated_client: TestClient):
    """Test get metrics endpoint with no providers."""
    client = authenticated_client
    with patch.object(client.app.state.app_state.metrics_collector, 'get_metrics', return_value={}), \
         patch.object(client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[]):

        response = client.get("/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["metrics"] == {}
        assert data["provider_details"] == []

def test_get_prometheus_metrics_success(authenticated_client: TestClient):
    """Test get prometheus metrics endpoint success."""
    client = authenticated_client
    prometheus_data = "# HELP ..."
    with patch.object(client.app.state.app_state.metrics_collector, 'get_prometheus_metrics', return_value=prometheus_data):
        response = client.get("/v1/analytics/prometheus")
        assert response.status_code == 200
        assert response.text == prometheus_data

def test_get_prometheus_metrics_no_api_key(client: TestClient):
    """Test get prometheus metrics endpoint without API key."""
    response = client.get("/v1/analytics/prometheus")
    assert response.status_code == 403

def test_get_prometheus_metrics_invalid_api_key(client: TestClient):
    """Test get prometheus metrics endpoint with invalid API key."""
    headers = {"X-API-Key": "invalid_key"}
    response = client.get("/v1/analytics/prometheus", headers=headers)
    assert response.status_code == 401

def test_get_prometheus_metrics_empty(authenticated_client: TestClient):
    """Test get prometheus metrics endpoint with empty data."""
    client = authenticated_client
    with patch.object(client.app.state.app_state.metrics_collector, 'get_prometheus_metrics', return_value=""):
        response = client.get("/v1/analytics/prometheus")
        assert response.status_code == 200
        assert response.text == ""

def test_metrics_with_provider_errors(authenticated_client: TestClient):
    """Test metrics endpoint with providers having errors."""
    client = authenticated_client
    mock_stats = {
        "openai": {"total_requests": 100, "success_rate": 0.8, "error_count": 20}
    }

    mock_provider = ProviderInfo(
        name="openai",
        type=ProviderType.OPENAI,
        status=ProviderStatus.DEGRADED,
        models=[],
        priority=1,
        enabled=True,
        forced=False,
        last_health_check=time.time(),
        error_count=20
    )

    with patch.object(client.app.state.app_state.metrics_collector, 'get_metrics', return_value=mock_stats), \
         patch.object(client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[mock_provider]):

        response = client.get("/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data["metrics"]
        assert data["provider_details"][0]["status"] == "degraded"

def test_metrics_with_forced_provider(authenticated_client: TestClient):
    """Test metrics endpoint with a forced provider."""
    client = authenticated_client
    mock_stats = {"openai": {"total_requests": 200, "success_rate": 0.9}}

    mock_provider = ProviderInfo(
        name="openai",
        type=ProviderType.OPENAI,
        status=ProviderStatus.HEALTHY,
        models=[],
        priority=1,
        enabled=True,
        forced=True,
        last_health_check=time.time(),
        error_count=0
    )

    with patch.object(client.app.state.app_state.metrics_collector, 'get_metrics', return_value=mock_stats), \
         patch.object(client.app.state.app_state.provider_factory, 'get_all_provider_info', new_callable=AsyncMock, return_value=[mock_provider]):

        response = client.get("/v1/analytics/metrics")
        assert response.status_code == 200
        data = response.json()
        assert data["provider_details"][0]["forced"] is True
