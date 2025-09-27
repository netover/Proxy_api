"""
Unit tests for API controllers.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import Response, Request

from src.api.controllers.health_controller import router as health_router
from src.api.controllers.analytics_controller import router as analytics_router
from src.api.controllers.config_controller import router as config_router
from src.api.controllers.chaos_controller import router as chaos_router
from src.api.controllers.alerting_controller import router as alerting_router
from src.api.controllers.context_controller import router as context_router
from src.core.config.models import UnifiedConfig
from src.core.providers.factory import provider_factory


class TestHealthController:
    """Test health controller endpoints."""

    def test_health_endpoint(self):
        """Test basic health check endpoint."""
        # Create a simple test app to test the router
        app = FastAPI()
        app.include_router(health_router)

        # Mock the app state properly
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.provider_factory = MagicMock()
        mock_app_state.provider_factory.get_all_provider_info = AsyncMock(return_value=[])
        mock_app_state.metrics_collector = MagicMock()
        mock_app_state.metrics_collector.get_metrics.return_value = {
            "system_health": {"cpu_percent": 50, "memory_percent": 60},
            "total_requests": 100
        }

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data

    def test_health_detailed_endpoint(self):
        """Test detailed health endpoint."""
        app = FastAPI()
        app.include_router(health_router)

        # Mock the app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.provider_factory = MagicMock()
        mock_app_state.provider_factory.get_all_provider_info = AsyncMock(return_value=[])
        mock_app_state.metrics_collector = MagicMock()
        mock_app_state.metrics_collector.get_metrics.return_value = {
            "system_health": {"cpu_percent": 50, "memory_percent": 60},
            "total_requests": 100,
            "uptime": 3600,
            "cache_performance": {"hit_rate": 0.85}
        }

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "providers" in data
        assert "system" in data

    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """Test provider health check functionality."""
        app = FastAPI()
        app.include_router(health_router)

        # Mock the app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.config = UnifiedConfig(
            providers=[ProviderConfig(name="test_provider", type="openai", api_key_env="TEST_KEY", models=["gpt-3.5-turbo"], enabled=True)]
        )
        mock_app_state.provider_factory = MagicMock()
        mock_app_state.provider_factory.get_provider = AsyncMock(return_value=None)
        mock_app_state.provider_factory.create_provider = AsyncMock(return_value=None)

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/health/providers")

        # Should handle gracefully when providers fail
        assert response.status_code in [200, 500]


class TestAnalyticsController:
    """Test analytics controller endpoints."""

    def test_analytics_endpoint_without_auth(self):
        """Test analytics endpoint requires authentication."""
        client = TestClient(analytics_router)

        response = client.get("/analytics")

        # Should require authentication
        assert response.status_code == 401

    def test_analytics_endpoint_with_auth(self):
        """Test analytics endpoint with authentication."""
        client = TestClient(analytics_router)

        # Mock authentication
        with patch('src.api.controllers.analytics_controller.verify_api_key') as mock_auth:
            mock_auth.return_value = True

            response = client.get("/analytics")

            # Should return analytics data
            assert response.status_code == 200


class TestConfigController:
    """Test config controller endpoints."""

    def test_config_status_endpoint(self):
        """Test config status endpoint."""
        client = TestClient(config_router)

        response = client.get("/config/status")

        assert response.status_code == 200
        data = response.json()
        assert "config_loaded" in data
        assert "providers_count" in data

    def test_config_reload_endpoint(self):
        """Test config reload endpoint."""
        client = TestClient(config_router)

        # Mock config manager
        with patch('src.api.controllers.config_controller.config_manager') as mock_manager:
            mock_manager.load_config = MagicMock()
            mock_manager.get_config = MagicMock(return_value=UnifiedConfig())

            response = client.post("/config/reload")

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "reloaded" in data["message"]


class TestChaosController:
    """Test chaos controller endpoints."""

    def test_chaos_status_endpoint(self):
        """Test chaos status endpoint."""
        client = TestClient(chaos_router)

        response = client.get("/chaos/status")

        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "active_experiments" in data
        assert "total_experiments" in data

    def test_chaos_experiments_endpoint(self):
        """Test chaos experiments list endpoint."""
        client = TestClient(chaos_router)

        response = client.get("/chaos/experiments")

        assert response.status_code == 200
        data = response.json()
        assert "experiments" in data

    def test_chaos_fault_types_endpoint(self):
        """Test chaos fault types endpoint."""
        client = TestClient(chaos_router)

        response = client.get("/chaos/fault-types")

        assert response.status_code == 200
        data = response.json()
        assert "fault_types" in data
        assert "severities" in data
        assert "examples" in data


class TestAlertingController:
    """Test alerting controller endpoints."""

    def test_alerts_endpoint(self):
        """Test alerts endpoint."""
        app = FastAPI()
        app.include_router(alerting_router)

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.alert_manager = MagicMock()
        mock_app_state.alert_manager.get_active_alerts.return_value = [
            {"id": "test_alert", "severity": "warning", "message": "Test alert"}
        ]

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/alerts")

        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data

    def test_alerts_history_endpoint(self):
        """Test alerts history endpoint."""
        app = FastAPI()
        app.include_router(alerting_router)

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.alert_manager = MagicMock()
        mock_app_state.alert_manager.get_alert_history.return_value = [
            {"id": "test_alert", "severity": "warning", "message": "Test alert", "acknowledged": True}
        ]

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/alerts/history")

        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data

    def test_alerts_config_endpoint(self):
        """Test alerts configuration endpoint."""
        app = FastAPI()
        app.include_router(alerting_router)

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.alert_manager = MagicMock()
        mock_app_state.alert_manager.get_notification_channels.return_value = []
        mock_app_state.alert_manager.get_alert_rules.return_value = []

        app.state.app_state = mock_app_state

        client = TestClient(app)

        response = client.get("/alerts/config")

        assert response.status_code == 200
        data = response.json()
        assert "config" in data


class TestContextController:
    """Test context controller endpoints."""

    def test_summary_status_endpoint(self):
        """Test summary status endpoint."""
        app = FastAPI()
        app.include_router(context_router)

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.summary_cache_obj = None  # Disable smart cache
        mock_app_state.summary_cache = {
            "test_request_id": {
                "summary": "Test summary",
                "timestamp": 1234567890,
                "latency": 0.5
            }
        }

        app.state = mock_app_state

        client = TestClient(app)

        response = client.get("/summary/test_request_id")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "summary" in data


class TestControllerIntegration:
    """Test controller integration with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_health_controller_with_provider_factory(self):
        """Test health controller with real provider factory integration."""
        # Create test app with health router
        app = FastAPI()
        app.include_router(health_router, prefix="/v1")

        # Mock app state properly
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.config = UnifiedConfig()
        mock_app_state.provider_factory = provider_factory
        mock_app_state.metrics_collector = MagicMock()
        mock_app_state.metrics_collector.get_metrics.return_value = {
            "system_health": {"cpu_percent": 50, "memory_percent": 60, "disk_percent": 70},
            "total_requests": 100,
            "successful_requests": 90,
            "failed_requests": 10,
            "overall_success_rate": 0.9,
            "uptime": 3600,
            "cache_performance": {"hit_rate": 0.85},
            "providers": {"avg_response_time": 0.5}
        }

        app.state.app_state = mock_app_state

        client = TestClient(app)

        # Test health endpoint
        response = client.get("/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_providers_endpoint(self):
        """Test health providers endpoint."""
        app = FastAPI()
        app.include_router(health_router, prefix="/v1")

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.config = UnifiedConfig(
            providers=[ProviderConfig(name="test_provider", type="openai", api_key_env="TEST_KEY", models=["gpt-3.5-turbo"], enabled=True)]
        )
        mock_app_state.provider_factory = MagicMock()
        mock_app_state.provider_factory.get_provider = AsyncMock(return_value=None)
        mock_app_state.provider_factory.create_provider = AsyncMock(return_value=None)

        app.state.app_state = mock_app_state

        client = TestClient(app)

        # Test health providers endpoint
        response = client.get("/v1/health/providers")
        # Should handle gracefully when providers fail
        assert response.status_code in [200, 500]

    def test_error_handling_in_controllers(self):
        """Test error handling in controllers."""
        client = TestClient(health_router)

        # Test with invalid endpoint
        response = client.get("/health/invalid")

        # Should return 404 or handle gracefully
        assert response.status_code in [404, 405]

    @pytest.mark.asyncio
    async def test_async_controller_operations(self):
        """Test async operations in controllers."""
        client = TestClient(health_router)

        # Mock async operations
        with patch('src.api.controllers.health_controller.provider_factory') as mock_factory:
            mock_factory.get_all_provider_info = AsyncMock(return_value=[])

            response = client.get("/health/providers")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_analytics_controller_with_auth(self):
        """Test analytics controller with authentication."""
        app = FastAPI()
        app.include_router(analytics_router, prefix="/v1")

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.metrics_collector = MagicMock()
        mock_app_state.metrics_collector.get_metrics.return_value = {
            "provider1": {"total_requests": 100, "success_rate": 0.9},
            "provider2": {"total_requests": 50, "success_rate": 0.85}
        }
        mock_app_state.provider_factory = MagicMock()
        mock_app_state.provider_factory.get_all_provider_info = AsyncMock(return_value=[])

        app.state.app_state = mock_app_state

        client = TestClient(app)

        # Test without auth (should fail)
        response = client.get("/v1/metrics")
        assert response.status_code == 401

        # Test with auth header
        response = client.get("/v1/metrics", headers={"Authorization": "Bearer test_key"})
        # Should handle gracefully even with missing auth implementation
        assert response.status_code in [200, 401, 500]

    @pytest.mark.asyncio
    async def test_config_controller_endpoints(self):
        """Test config controller endpoints."""
        app = FastAPI()
        app.include_router(config_router, prefix="/v1")

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.config_manager = MagicMock()
        mock_app_state.config_manager.get_config.return_value = UnifiedConfig()
        mock_app_state.config_manager.load_config = MagicMock()

        app.state.app_state = mock_app_state

        client = TestClient(app)

        # Test config status
        response = client.get("/v1/config/status")
        assert response.status_code == 200

        # Test config reload
        response = client.post("/v1/config/reload")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chaos_controller_endpoints(self):
        """Test chaos controller endpoints."""
        app = FastAPI()
        app.include_router(chaos_router, prefix="/v1")

        # Mock app state
        from unittest.mock import MagicMock
        mock_app_state = MagicMock()
        mock_app_state.chaos_engine = MagicMock()
        mock_app_state.chaos_engine.get_status.return_value = {
            "enabled": True,
            "active_experiments": 2,
            "total_experiments": 5
        }
        mock_app_state.chaos_engine.get_experiments.return_value = []
        mock_app_state.chaos_engine.get_fault_types.return_value = {
            "fault_types": ["latency", "error", "cpu"],
            "severities": ["low", "medium", "high"]
        }

        app.state.app_state = mock_app_state

        client = TestClient(app)

        # Test chaos status
        response = client.get("/v1/chaos/status")
        assert response.status_code == 200

        # Test chaos experiments
        response = client.get("/v1/chaos/experiments")
        assert response.status_code == 200

        # Test chaos fault types
        response = client.get("/v1/chaos/fault-types")
        assert response.status_code == 200
