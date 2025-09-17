import pytest
import os
from unittest.mock import patch
from fastapi.testclient import TestClient

from src.core.auth import APIKeyAuth
from main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

class TestAuth:
    def test_verify_api_key_success(self, client):
        api_keys = ["test-key-1"]
        with patch.object(app.state.app_state, "api_key_auth", APIKeyAuth(api_keys)):
            response = client.get("/v1/models", headers={"X-API-Key": "test-key-1"})
            # This endpoint might not exist, but we are testing auth, not the endpoint itself
            # A 404 Not Found error means the request was authenticated
            # A 403 or 401 would mean auth failed
            assert response.status_code != 401
            assert response.status_code != 403

    def test_verify_api_key_failure(self, client):
        response = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
        print(response.json())
        assert response.status_code == 401

    def test_load_keys_from_env(self, client):
        os.environ["PROXY_API_KEYS"] = "env-key-1,env-key-2"
        # We need to re-initialize the app_state to pick up the new env var
        from src.core.app_state import app_state
        app.state.app_state.api_key_auth = APIKeyAuth(app_state.config.proxy_api_keys)

        response = client.get("/v1/models", headers={"X-API-Key": "env-key-1"})
        assert response.status_code != 401

        response = client.get("/v1/models", headers={"X-API-Key": "env-key-2"})
        assert response.status_code != 401

        response = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401

        del os.environ["PROXY_API_KEYS"]
