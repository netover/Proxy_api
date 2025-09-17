import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(scope="module")
def client():
    """
    Test client for FastAPI app that correctly handles lifespan events.
    """
    with TestClient(app) as test_client:
        yield test_client
