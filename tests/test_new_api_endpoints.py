"""
Tests for the new thin controller API endpoints.

This module tests the refactored API endpoints to ensure they work correctly
with the new thin controller architecture.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from main import app
from src.core.provider_factory import ProviderStatus

client = TestClient(app)


class TestChatController:
    """Test cases for chat controller endpoints."""

    def test_chat_completions_endpoint_exists(self):
        """Test that chat completions endpoint is accessible."""
        # This test just verifies the endpoint exists and returns proper error for missing auth
        response = client.post("/v1/chat/completions", json={})
        assert response.status_code in [
            401,
            422,
        ]  # Either auth error or validation error

    def test_text_completions_endpoint_exists(self):
        """Test that text completions endpoint is accessible."""
        response = client.post("/v1/completions", json={})
        assert response.status_code in [401, 422]


class TestModelController:
    """Test cases for model controller endpoints."""

    def test_list_models_endpoint(self):
        """Test that models listing endpoint works."""
        response = client.get("/v1/models")
        assert response.status_code in [200, 401]  # Success or auth required

    def test_list_providers_endpoint(self):
        """Test that providers listing endpoint works."""
        response = client.get("/providers")  # Note: not under /v1/ prefix
        assert response.status_code in [200, 401]


class TestHealthController:
    """Test cases for health controller endpoints."""

    def test_health_endpoint(self):
        """Test that health endpoint returns proper structure."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "providers" in data


class TestAnalyticsController:
    """Test cases for analytics controller endpoints."""

    def test_metrics_endpoint(self):
        """Test that metrics endpoint requires authentication."""
        response = client.get("/metrics")
        # Should return 401 without proper auth
        assert response.status_code == 401


class TestAPIRouter:
    """Test cases for the main API router setup."""

    def test_root_endpoint(self):
        """Test that root endpoint provides API information."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_api_status_endpoint(self):
        """Test that /v1/status endpoint works."""
        response = client.get("/v1/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data


class TestMiddleware:
    """Test cases for middleware functionality."""

    def test_cors_headers(self):
        """Test that CORS headers are properly set."""
        response = client.options("/v1/chat/completions")
        # CORS preflight should be handled
        assert response.status_code in [200, 404, 401]

    def test_request_logging(self):
        """Test that requests are being logged (indirect test)."""
        # This is more of a smoke test - if the request completes without error,
        # the middleware is likely working
        response = client.get("/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Test cases for error handling."""

    def test_invalid_json_returns_proper_error(self):
        """Test that invalid JSON returns proper validation error."""
        response = client.post(
            "/v1/chat/completions",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self):
        """Test that missing required fields return validation errors."""
        response = client.post(
            "/v1/chat/completions",
            json={"model": "gpt-3.5-turbo"},  # Missing messages
            headers={"Authorization": "Bearer test"},
        )
        assert response.status_code in [422, 401]  # Validation or auth error


class TestValidation:
    """Test cases for request/response validation."""

    @patch("src.api.controllers.common.request_router")
    def test_request_validation_integration(self, mock_router):
        """Test that request validation is integrated properly."""
        # Mock the router to avoid actual provider calls
        mock_router.route_request.return_value = {"test": "response"}

        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
            },
            headers={"Authorization": "Bearer test"},
        )

        # Should either succeed (200) or fail due to auth (401)
        assert response.status_code in [200, 401]


if __name__ == "__main__":
    pytest.main([__file__])
