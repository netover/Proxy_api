import pytest
from starlette.testclient import TestClient

# Fixtures from conftest.py (client, authenticated_client) are used.
# They now create a fresh app and state for each test.

class TestAPIKeyAuthentication:
    """Tests API key authentication with isolated, function-scoped fixtures."""

    def test_no_api_key_provided_fails(self, client: TestClient):
        """
        If no API key is provided, it should fail with 403 Forbidden.
        The `client` fixture provides an app with PROXY_API_KEYS unset.
        """
        response = client.get("/v1/models")
        assert response.status_code == 403
        assert "Not authenticated" in response.json().get("detail")

    def test_no_keys_configured_on_server_rejects_all(self, client: TestClient):
        """
        If the server has no keys configured, any provided key is invalid.
        The `client` fixture provides an app with PROXY_API_KEYS unset.
        """
        response = client.get("/v1/models", headers={"X-API-Key": "any-key-will-fail"})
        assert response.status_code == 401
        assert "Invalid API Key" in response.json().get("detail")

    def test_single_api_key_in_env_is_validated(self, monkeypatch, client: TestClient):
        """
        Tests that a single API key from the environment is correctly loaded and validated.
        """
        # Set the environment variable. The `client` fixture will create a new app
        # instance that reads this environment variable upon initialization.
        monkeypatch.setenv("PROXY_API_KEYS", "secret-key-1")

        # Re-create the client to pick up the new env var
        from src.bootstrap import app
        with TestClient(app) as new_client:
            # Test the valid key
            response_ok = new_client.get("/v1/models", headers={"X-API-Key": "secret-key-1"})
            assert response_ok.status_code == 200

            # Test an invalid key
            response_fail = new_client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
            assert response_fail.status_code == 401

    def test_multiple_api_keys_in_env_are_validated(self, monkeypatch):
        """
        Tests that multiple comma-separated keys from the environment are loaded.
        """
        monkeypatch.setenv("PROXY_API_KEYS", "key1,key2,key3")
        from src.bootstrap import app
        with TestClient(app) as client:
            # Test all valid keys
            for key in ["key1", "key2", "key3"]:
                response = client.get("/v1/models", headers={"X-API-Key": key})
                assert response.status_code == 200, f"Key '{key}' should have been accepted"

            # Test an invalid key
            response_fail = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
            assert response_fail.status_code == 401

    def test_keys_with_whitespace_are_trimmed(self, monkeypatch):
        """
        Tests that keys with leading/trailing whitespace are correctly trimmed.
        """
        monkeypatch.setenv("PROXY_API_KEYS", "  spaced-key  ,  another-spaced-key  ")
        from src.bootstrap import app
        with TestClient(app) as client:
            # Test that the trimmed keys work
            response_ok1 = client.get("/v1/models", headers={"X-API-Key": "spaced-key"})
            assert response_ok1.status_code == 200

            response_ok2 = client.get("/v1/models", headers={"X-API-Key": "another-spaced-key"})
            assert response_ok2.status_code == 200

            # Test that the untrimmed key fails because the header value is used as-is
            response_fail = client.get("/v1/models", headers={"X-API-Key": "  spaced-key  "})
            assert response_fail.status_code == 401
