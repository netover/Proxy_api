from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpointHTTPMethods:
    """Test all HTTP methods for health endpoints."""

    def test_health_get_success(self):
        """Test GET /health success."""
        # Mock the app state and provider factory
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.status.value = "healthy"
            mock_provider.name = "test_provider"
            mock_provider.type.value = "openai"
            mock_provider.models = ["gpt-4"]
            mock_provider.enabled = True
            mock_provider.forced = False
            mock_provider.last_health_check = 1234567890
            mock_provider.error_count = 0
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            response = client.get("/health")
            assert response.status_code == 200
            json_response = response.json()
            assert "status" in json_response
            assert "providers" in json_response

    def test_health_post_method_not_allowed(self):
        """Test POST /health returns 405 Method Not Allowed."""
        response = client.post("/health")
        assert response.status_code == 405

    def test_health_put_method_not_allowed(self):
        """Test PUT /health returns 405 Method Not Allowed."""
        response = client.put("/health")
        assert response.status_code == 405

    def test_health_delete_method_not_allowed(self):
        """Test DELETE /health returns 405 Method Not Allowed."""
        response = client.delete("/health")
        assert response.status_code == 405

    def test_health_patch_method_not_allowed(self):
        """Test PATCH /health returns 405 Method Not Allowed."""
        response = client.patch("/health")
        assert response.status_code == 405

    def test_health_options_method_not_allowed(self):
        """Test OPTIONS /health returns 405 Method Not Allowed."""
        response = client.options("/health")
        assert response.status_code == 405

    def test_root_health_get_success(self):
        """Test GET /health (root level) success."""
        response = client.get("/health")
        assert response.status_code == 200
        json_response = response.json()
        assert "status" in json_response
        assert "service" in json_response
        assert json_response["service"] == "proxy-api-gateway"


class TestChatEndpointHTTPMethods:
    """Test all HTTP methods for chat endpoints."""

    def test_chat_completions_post_success(self):
        """Test POST /v1/chat/completions success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.create_completion.return_value = {
                "id": "chatcmpl_test",
                "choices": [{"message": {"content": "Test response"}}],
                "model": "gpt-4",
            }
            mock_provider_factory.get_providers_for_model.return_value = [mock_provider]
            mock_provider_factory.get_provider.return_value = mock_provider
            mock_app_state.provider_factory = mock_provider_factory

            data = {
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
            }
            headers = {"Authorization": "Bearer test_key"}
            response = client.post("/v1/chat/completions", json=data, headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "choices" in json_response
            assert json_response["choices"][0]["message"]["content"] == "Test response"

    def test_chat_completions_get_method_not_allowed(self):
        """Test GET /v1/chat/completions returns 405 Method Not Allowed."""
        response = client.get("/v1/chat/completions")
        assert response.status_code == 405

    def test_chat_completions_put_method_not_allowed(self):
        """Test PUT /v1/chat/completions returns 405 Method Not Allowed."""
        response = client.put("/v1/chat/completions")
        assert response.status_code == 405

    def test_chat_completions_delete_method_not_allowed(self):
        """Test DELETE /v1/chat/completions returns 405 Method Not Allowed."""
        response = client.delete("/v1/chat/completions")
        assert response.status_code == 405

    def test_chat_completions_patch_method_not_allowed(self):
        """Test PATCH /v1/chat/completions returns 405 Method Not Allowed."""
        response = client.patch("/v1/chat/completions")
        assert response.status_code == 405


class TestModelsEndpointHTTPMethods:
    """Test all HTTP methods for models endpoints."""

    def test_models_get_success(self):
        """Test GET /v1/models success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.status.value = "healthy"
            mock_provider.name = "openai"
            mock_provider.type.value = "openai"
            mock_provider.models = ["gpt-4", "gpt-3.5-turbo"]
            mock_provider.enabled = True
            mock_provider.forced = False
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            response = client.get("/v1/models")
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) == 2
            assert json_response["data"][0]["id"] == "gpt-4"

    def test_models_post_method_not_allowed(self):
        """Test POST /v1/models returns 405 Method Not Allowed."""
        response = client.post("/v1/models")
        assert response.status_code == 405

    def test_models_put_method_not_allowed(self):
        """Test PUT /v1/models returns 405 Method Not Allowed."""
        response = client.put("/v1/models")
        assert response.status_code == 405

    def test_models_delete_method_not_allowed(self):
        """Test DELETE /v1/models returns 405 Method Not Allowed."""
        response = client.delete("/v1/models")
        assert response.status_code == 405

    def test_models_patch_method_not_allowed(self):
        """Test PATCH /v1/models returns 405 Method Not Allowed."""
        response = client.patch("/v1/models")
        assert response.status_code == 405


class TestConfigEndpointHTTPMethods:
    """Test all HTTP methods for config endpoints."""

    def test_config_reload_post_success(self):
        """Test POST /v1/config/reload success."""
        with patch(
            "src.api.controllers.config_controller.config_manager"
        ) as mock_config_manager:
            mock_config = Mock()
            mock_config.settings.app_version = "1.0.0"
            mock_config_manager.load_config.return_value = mock_config

            headers = {"Authorization": "Bearer test_key"}
            response = client.post("/v1/config/reload", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "success" in json_response
            assert json_response["success"] is True

    def test_config_reload_get_method_not_allowed(self):
        """Test GET /v1/config/reload returns 405 Method Not Allowed."""
        response = client.get("/v1/config/reload")
        assert response.status_code == 405

    def test_config_reload_put_method_not_allowed(self):
        """Test PUT /v1/config/reload returns 405 Method Not Allowed."""
        response = client.put("/v1/config/reload")
        assert response.status_code == 405

    def test_config_reload_delete_method_not_allowed(self):
        """Test DELETE /v1/config/reload returns 405 Method Not Allowed."""
        response = client.delete("/v1/config/reload")
        assert response.status_code == 405

    def test_config_reload_patch_method_not_allowed(self):
        """Test PATCH /v1/config/reload returns 405 Method Not Allowed."""
        response = client.patch("/v1/config/reload")
        assert response.status_code == 405

    def test_config_status_get_success(self):
        """Test GET /v1/config/status success."""
        with patch(
            "src.api.controllers.config_controller.config_manager"
        ) as mock_config_manager:
            mock_config_manager.config_path.exists.return_value = True
            mock_config_manager.config_path.stat.return_value.st_mtime = 1234567890

            headers = {"Authorization": "Bearer test_key"}
            response = client.get("/v1/config/status", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "current_config_path" in json_response
            assert "cache_status" in json_response

    def test_config_status_post_method_not_allowed(self):
        """Test POST /v1/config/status returns 405 Method Not Allowed."""
        response = client.post("/v1/config/status")
        assert response.status_code == 405


class TestMetricsEndpointHTTPMethods:
    """Test all HTTP methods for metrics endpoints."""

    def test_metrics_get_success(self):
        """Test GET /v1/metrics success."""
        with patch(
            "src.api.controllers.analytics_controller.metrics_collector"
        ) as mock_collector, patch(
            "src.bootstrap.app_state", Mock()
        ) as mock_app_state:
            mock_stats = {"openai": {"total_requests": 10, "success_rate": 0.9}}
            mock_collector.get_all_stats.return_value = mock_stats
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.name = "openai"
            mock_provider.status.value = "healthy"
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            headers = {"Authorization": "Bearer test_key"}
            response = client.get("/v1/metrics", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "providers" in json_response
            assert "openai" in json_response["providers"]

    def test_metrics_post_method_not_allowed(self):
        """Test POST /v1/metrics returns 405 Method Not Allowed."""
        response = client.post("/v1/metrics")
        assert response.status_code == 405

    def test_metrics_prometheus_get_success(self):
        """Test GET /v1/metrics/prometheus success."""
        with patch(
            "src.api.controllers.analytics_controller.metrics_collector"
        ) as mock_collector:
            mock_collector.get_prometheus_metrics.return_value = "# Prometheus metrics"

            headers = {"Authorization": "Bearer test_key"}
            response = client.get("/v1/metrics/prometheus", headers=headers)
            assert response.status_code == 200
            assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_prometheus_post_method_not_allowed(self):
        """Test POST /v1/metrics/prometheus returns 405 Method Not Allowed."""
        response = client.post("/v1/metrics/prometheus")
        assert response.status_code == 405


class TestProvidersEndpointHTTPMethods:
    """Test all HTTP methods for providers endpoints."""

    def test_providers_get_success(self):
        """Test GET /v1/providers success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.name = "openai"
            mock_provider.type.value = "openai"
            mock_provider.status.value = "healthy"
            mock_provider.models = ["gpt-4"]
            mock_provider.priority = 1
            mock_provider.enabled = True
            mock_provider.forced = False
            mock_provider.last_health_check = 1234567890
            mock_provider.error_count = 0
            mock_provider.last_error = None
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            headers = {"Authorization": "Bearer test_key"}
            response = client.get("/v1/providers", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "providers" in json_response
            assert len(json_response["providers"]) == 1
            assert json_response["providers"][0]["name"] == "openai"

    def test_providers_post_method_not_allowed(self):
        """Test POST /v1/providers returns 405 Method Not Allowed."""
        response = client.post("/v1/providers")
        assert response.status_code != 200


class TestModelManagementEndpointHTTPMethods:
    """Test all HTTP methods for model management endpoints."""

    def test_provider_models_get_success(self):
        """Test GET /v1/providers/{provider_name}/models success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state, patch(
            "src.api.model_endpoints.app_state.model_discovery"
        ) as mock_discovery:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.name = "openai"
            mock_provider.base_url = "https://api.openai.com/v1"
            mock_provider.api_key = "test_key"
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            mock_model = Mock()
            mock_model.id = "gpt-4"
            mock_model.created = 1234567890
            mock_model.owned_by = "openai"
            mock_discovery.discover_models.return_value = [mock_model]

            headers = {"Authorization": "Bearer test_key"}
            response = client.get("/v1/providers/openai/models", headers=headers)
            assert response.status_code == 200
            json_response = response.json()
            assert "data" in json_response
            assert len(json_response["data"]) == 1

    def test_provider_models_post_method_not_allowed(self):
        """Test POST /v1/providers/{provider_name}/models returns 405 Method Not Allowed."""
        response = client.post("/v1/providers/openai/models")
        assert response.status_code != 200

    def test_provider_model_selection_put_success(self):
        """Test PUT /v1/providers/{provider_name}/model_selection success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state, patch(
            "src.api.model_endpoints.app_state.model_discovery"
        ) as mock_discovery, patch(
            "src.api.model_endpoints.app_state.config_manager"
        ) as mock_config_manager:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.name = "openai"
            mock_provider.base_url = "https://api.openai.com/v1"
            mock_provider.api_key = "test_key"
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            mock_model = Mock()
            mock_model.id = "gpt-4"
            mock_discovery.get_model_info.return_value = mock_model

            mock_config = Mock()
            mock_config_manager.load_config.return_value = mock_config
            mock_config_manager.save_config.return_value = None

            data = {"selected_model": "gpt-4", "editable": True, "priority": 1}
            headers = {"Authorization": "Bearer test_key"}
            response = client.put(
                "/v1/providers/openai/model_selection",
                json=data,
                headers=headers,
            )
            assert response.status_code == 200
            json_response = response.json()
            assert "success" in json_response
            assert json_response["success"] is True

    def test_provider_model_selection_get_method_not_allowed(self):
        """Test GET /v1/providers/{provider_name}/model_selection returns 405 Method Not Allowed."""
        response = client.get("/v1/providers/openai/model_selection")
        assert response.status_code != 200

    def test_provider_models_refresh_post_success(self):
        """Test POST /v1/providers/{provider_name}/models/refresh success."""
        with patch("src.bootstrap.app_state", Mock()) as mock_app_state, patch(
            "src.api.model_endpoints.app_state.model_discovery"
        ) as mock_discovery, patch(
            "src.api.model_endpoints.app_state.cache_manager"
        ) as mock_cache_manager:
            mock_provider_factory = Mock()
            mock_provider = Mock()
            mock_provider.name = "openai"
            mock_provider.base_url = "https://api.openai.com/v1"
            mock_provider.api_key = "test_key"
            mock_provider_factory.get_all_provider_info.return_value = [mock_provider]
            mock_app_state.provider_factory = mock_provider_factory

            mock_model = Mock()
            mock_model.id = "gpt-4"
            mock_discovery.discover_models.return_value = [mock_model]
            mock_cache_manager.clear_provider_cache.return_value = True

            headers = {"Authorization": "Bearer test_key"}
            response = client.post(
                "/v1/providers/openai/models/refresh", headers=headers
            )
            assert response.status_code == 200
            json_response = response.json()
            assert "success" in json_response
            assert json_response["success"] is True

    def test_provider_models_refresh_get_method_not_allowed(self):
        """Test GET /v1/providers/{provider_name}/models/refresh returns 405 Method Not Allowed."""
        response = client.get("/v1/providers/openai/models/refresh")
        assert response.status_code != 200


class TestCacheEndpointHTTPMethods:
    """Test all HTTP methods for cache endpoints."""

    def test_cache_stats_get_success(self):
        """Test GET /v1/cache/stats success."""
        with patch("src.core.unified_cache.get_unified_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.get_stats.return_value = {
                "entries": 100,
                "hit_rate": 0.85,
            }
            mock_get_cache.return_value = mock_cache

            response = client.get("/v1/cache/stats")
            assert response.status_code == 200
            json_response = response.json()
            assert "unified_cache" in json_response
            assert json_response["unified_cache"]["entries"] == 100

    def test_cache_clear_post_success(self):
        """Test POST /v1/cache/clear success."""
        with patch("src.core.unified_cache.get_unified_cache") as mock_get_cache:
            mock_cache = Mock()
            mock_cache.clear.return_value = 50
            mock_get_cache.return_value = mock_cache

            response = client.post("/v1/cache/clear")
            assert response.status_code == 200
            json_response = response.json()
            assert "unified_cache_cleared" in json_response
            assert json_response["unified_cache_cleared"] == 50

    def test_cache_clear_get_method_not_allowed(self):
        """Test GET /v1/cache/clear returns 405 Method Not Allowed."""
        response = client.get("/v1/cache/clear")
        assert response.status_code != 200

    def test_cache_health_get_success(self):
        """Test GET /v1/cache/health success."""
        with patch("src.core.cache_monitor.get_cache_health_report") as mock_health:
            mock_health.return_value = {"status": "healthy", "hit_rate": 0.9}

            response = client.get("/v1/cache/health")
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["status"] == "healthy"

    def test_cache_warmup_post_success(self):
        """Test POST /v1/cache/warmup success."""
        with patch("src.core.cache_monitor.warmup_cache") as mock_warmup:
            mock_warmup.return_value = {"warmed_entries": 25}

            response = client.post("/v1/cache/warmup")
            assert response.status_code == 200
            json_response = response.json()
            assert "results" in json_response

    def test_cache_monitor_start_post_success(self):
        """Test POST /v1/cache/monitor/start success."""
        with patch("src.core.cache_monitor.start_monitoring") as mock_start:
            mock_start.return_value = None

            response = client.post("/v1/cache/monitor/start")
            assert response.status_code == 200
            json_response = response.json()
            assert "message" in json_response

    def test_cache_monitor_stop_post_success(self):
        """Test POST /v1/cache/monitor/stop success."""
        with patch("src.core.cache_monitor.stop_monitoring") as mock_stop:
            mock_stop.return_value = None

            response = client.post("/v1/cache/monitor/stop")
            assert response.status_code == 200
            json_response = response.json()
            assert "message" in json_response


class TestRootEndpointHTTPMethods:
    """Test all HTTP methods for root endpoints."""

    def test_root_get_success(self):
        """Test GET / success."""
        response = client.get("/")
        assert response.status_code == 200
        json_response = response.json()
        assert "name" in json_response
        assert "version" in json_response
        assert "endpoints" in json_response

    def test_root_post_method_not_allowed(self):
        """Test POST / returns 405 Method Not Allowed."""
        response = client.post("/")
        assert response.status_code == 405

    def test_api_status_get_success(self):
        """Test GET /v1/status success."""
        response = client.get("/v1/status")
        assert response.status_code == 200
        json_response = response.json()
        assert "status" in json_response
        assert "version" in json_response
        assert "features" in json_response

    def test_api_status_post_method_not_allowed(self):
        """Test POST /v1/status returns 405 Method Not Allowed."""
        response = client.post("/v1/status")
        assert response.status_code == 405


class TestAuthenticationRequirements:
    """Test authentication requirements for protected endpoints."""

    def test_protected_endpoint_without_auth(self):
        """Test that protected endpoints require authentication."""
        data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        response = client.post("/v1/chat/completions", json=data)
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_auth(self):
        """Test protected endpoints with invalid authentication."""
        headers = {"Authorization": "Bearer invalid_key"}
        response = client.get("/v1/metrics", headers=headers)
        assert response.status_code == 401

    def test_public_endpoint_without_auth(self):
        """Test that public endpoints work without authentication."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_root_endpoint_without_auth(self):
        """Test root endpoint works without authentication."""
        response = client.get("/")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payloads."""
        headers = {
            "Authorization": "Bearer test_key",
            "Content-Type": "application/json",
        }
        response = client.post(
            "/v1/chat/completions", data="invalid json", headers=headers
        )
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        """Test handling of missing required fields."""
        headers = {"Authorization": "Bearer test_key"}
        data = {"model": "gpt-4"}  # Missing messages
        response = client.post("/v1/chat/completions", json=data, headers=headers)
        assert response.status_code == 422  # Validation error

    def test_unsupported_content_type(self):
        """Test handling of unsupported content types."""
        headers = {
            "Authorization": "Bearer test_key",
            "Content-Type": "text/plain",
        }
        data = "plain text data"
        response = client.post("/v1/chat/completions", data=data, headers=headers)
        assert response.status_code == 422  # Validation error

    def test_nonexistent_endpoint(self):
        """Test handling of nonexistent endpoints."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404

    def test_invalid_path_parameters(self):
        """Test handling of invalid path parameters."""
        headers = {"Authorization": "Bearer test_key"}
        response = client.get("/v1/providers/nonexistent/models", headers=headers)
        assert response.status_code == 404
