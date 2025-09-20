import pytest
from fastapi.testclient import TestClient

from src.core.auth import APIKeyAuth, verify_api_key
from main import app

# Use a single client fixture for all tests in this module
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_verify_api_key_success(client: TestClient):
    """
    Tests that a valid API key grants access.
    We override the dependency for the entire app with a specific set of keys.
    """
    # Define a specific set of API keys for this test
    api_keys = ["test-key-1"]
    auth_handler = APIKeyAuth(api_keys)

    # Use FastAPI's dependency override feature
    app.dependency_overrides[verify_api_key] = auth_handler.verify_api_key

    # Test against a simple, known endpoint
    response = client.get("/v1/models", headers={"X-API-Key": "test-key-1"})

    # A successful authentication should not result in a 401 or 403.
    # The actual status code will depend on the endpoint's implementation (e.g., 200 or 404).
    # This is sufficient to prove authentication passed.
    assert response.status_code not in [401, 403]

    # Clean up the override
    app.dependency_overrides = {}

def test_verify_api_key_failure_wrong_key(client: TestClient):
    """
    Tests that an invalid API key is rejected.
    """
    api_keys = ["test-key-1"]
    auth_handler = APIKeyAuth(api_keys)
    app.dependency_overrides[verify_api_key] = auth_handler.verify_api_key

    response = client.get("/v1/models", headers={"X-API-Key": "wrong-key"})

    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]

    app.dependency_overrides = {}

def test_verify_api_key_failure_no_key(client: TestClient):
    """
    Tests that a request without an API key is rejected.
    """
    api_keys = ["test-key-1"]
    auth_handler = APIKeyAuth(api_keys)
    app.dependency_overrides[verify_api_key] = auth_handler.verify_api_key

    response = client.get("/v1/models")

    assert response.status_code == 401
    assert "API key is missing" in response.json()["detail"]

    app.dependency_overrides = {}
