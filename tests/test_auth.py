import pytest
from starlette.testclient import TestClient
from src.bootstrap import create_app
from src.core.config.models import UnifiedConfig

class TestAPIKeyAuthentication:
    """
    Tests for the API Key Authentication logic, using the app factory pattern
    for proper test isolation.
    """

    def test_no_api_key_provided_fails(self, client: TestClient):
        """
        If no API key is provided to a protected endpoint, it should fail with 403 Forbidden.
        The `client` fixture provides an app with no API keys configured.
        """
        response = client.get("/v1/models")
        assert response.status_code == 403
        assert "Not authenticated" in response.text

    def test_no_keys_configured_on_server_rejects_all(self, client: TestClient):
        """
        If the server has no API keys configured, any key provided by the client
        should be rejected with 401 Unauthorized.
        """
        response = client.get("/v1/models", headers={"X-API-Key": "any-key-will-fail"})
        assert response.status_code == 401
        assert "Invalid API Key" in response.text

    def test_correct_api_key_is_accepted(self, authenticated_client: TestClient):
        """
        A valid API key provided in the header should be accepted.
        The `authenticated_client` is configured with 'test-key-123'.
        """
        # The /v1/models endpoint is protected and suitable for this check.
        # We expect a 500 error because no providers are configured in the base test config,
        # but a 200-level or 4xx-level code indicates auth success.
        response = authenticated_client.get("/v1/models")
        assert response.status_code != 401
        assert response.status_code != 403

    def test_incorrect_api_key_is_rejected(self, authenticated_client: TestClient):
        """
        An invalid API key should be rejected with 401 Unauthorized.
        """
        # The `authenticated_client` is configured with 'test-key-123'.
        # We send a different key to test the rejection.
        authenticated_client.headers["X-API-Key"] = "incorrect-key"
        response = authenticated_client.get("/v1/models")
        assert response.status_code == 401
        assert "Invalid API Key" in response.text

    def test_keys_with_whitespace_are_validated_correctly(self, test_config: UnifiedConfig):
        """
        Tests that keys with leading/trailing whitespace are correctly trimmed and validated.
        """
        keys_with_whitespace = ["  spaced-key  ", "  another-spaced-key"]
        test_config.proxy_api_keys = keys_with_whitespace

        app = create_app(test_config)

        with TestClient(app) as client:
            # Test the key that had whitespace on both sides
            response_ok1 = client.get("/v1/models", headers={"X-API-Key": "spaced-key"})
            assert response_ok1.status_code != 401
            assert response_ok1.status_code != 403

            # Test the key that had whitespace on one side
            response_ok2 = client.get("/v1/models", headers={"X-API-Key": "another-spaced-key"})
            assert response_ok2.status_code != 401
            assert response_ok2.status_code != 403

            # Test that a key without the correct spacing fails
            response_fail = client.get("/v1/models", headers={"X-API-Key": "  spaced-key  "})
            assert response_fail.status_code == 401