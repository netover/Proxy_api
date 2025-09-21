import pytest
from fastapi.testclient import TestClient

# The app from bootstrap is already configured. We import it once.
from src.bootstrap import app

@pytest.fixture(scope="function")
def client(monkeypatch):
    """
    Provides a fresh TestClient for each test.
    It ensures that the PROXY_API_KEYS env var is cleared before each run,
    and a new app instance with a fresh state is created.
    """
    monkeypatch.delenv("PROXY_API_KEYS", raising=False)
    with TestClient(app) as c:
        yield c

class TestAPIKeyAuthentication:
    """
    Tests the API key authentication, specifically loading keys from environment variables.
    These tests use a function-scoped client to ensure no state is leaked.
    The TestClient context manager re-runs the app's lifespan for each test,
    picking up any environment variables set by monkeypatch.
    """

    def test_no_api_key_provided_fails(self, client):
        """
        If no API key is provided in the request, it should fail with 403 Forbidden.
        The client fixture ensures PROXY_API_KEYS is unset.
        """
        response = client.get("/v1/models") # This endpoint is behind the auth middleware
        assert response.status_code == 403
        assert "Not authenticated" in response.json().get("detail")

    def test_no_keys_configured_on_server_rejects_all(self, client):
        """
        If the PROXY_API_KEYS env var is not set, all requests with keys should be denied.
        The client fixture ensures PROXY_API_KEYS is unset.
        """
        response = client.get("/v1/models", headers={"X-API-Key": "any-key-will-fail"})
        assert response.status_code == 401
        assert "Invalid API Key" in response.json().get("detail")

    def test_single_api_key_in_env_is_validated(self, monkeypatch):
        """
        Tests that a single API key from the environment is correctly loaded and validated.
        """
        monkeypatch.setenv("PROXY_API_KEYS", "secret-key-1")
        with TestClient(app) as client:
            # Test the valid key
            response_ok = client.get("/v1/models", headers={"X-API-Key": "secret-key-1"})
            assert response_ok.status_code != 401
            assert response_ok.status_code != 403

            # Test an invalid key
            response_fail = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
            assert response_fail.status_code == 401

    def test_multiple_api_keys_in_env_are_validated(self, monkeypatch):
        """
        Tests that multiple comma-separated keys from the environment are loaded.
        """
        monkeypatch.setenv("PROXY_API_KEYS", "key1,key2,key3")
        with TestClient(app) as client:
            # Test all valid keys
            for key in ["key1", "key2", "key3"]:
                response = client.get("/v1/models", headers={"X-API-Key": key})
                assert response.status_code != 401, f"Key '{key}' should have been accepted"

            # Test an invalid key
            response_fail = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
            assert response_fail.status_code == 401

    def test_keys_with_whitespace_are_trimmed(self, monkeypatch):
        """
        Tests that keys with leading/trailing whitespace are correctly trimmed.
        """
        monkeypatch.setenv("PROXY_API_KEYS", "  spaced-key  ,  another-spaced-key  ")
        with TestClient(app) as client:
            # Test that the trimmed keys work
            response_ok1 = client.get("/v1/models", headers={"X-API-Key": "spaced-key"})
            assert response_ok1.status_code != 401

            response_ok2 = client.get("/v1/models", headers={"X-API-Key": "another-spaced-key"})
            assert response_ok2.status_code != 401

            # Test that the untrimmed key fails because the header value is used as-is
            response_fail = client.get("/v1/models", headers={"X-API-Key": "  spaced-key  "})
            assert response_fail.status_code == 401
