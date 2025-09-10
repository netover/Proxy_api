import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming the FastAPI app is defined in main.py

client = TestClient(app)

def test_chat_completions_streaming():
    """Test streaming chat completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "stream": True
    }
    headers = {"Authorization": "Bearer test_key"}  # Use a test API key

    response = client.post("/v1/chat/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Verify SSE format in response
    lines = [line.decode('utf-8') for line in response.iter_lines() if line]
    assert len(lines) > 0
    assert any(line.startswith("data: ") for line in lines)
    # Check for end of stream
    assert any('data: [DONE]' in line for line in lines)

def test_chat_completions_non_streaming():
    """Test non-streaming chat completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello, world!"}],
        "stream": False
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/chat/completions", json=data, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    json_response = response.json()
    assert "choices" in json_response

def test_text_completions_streaming():
    """Test streaming text completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo-instruct",
        "prompt": "Hello, world!",
        "stream": True
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    # Verify SSE format in response
    lines = [line.decode('utf-8') for line in response.iter_lines() if line]
    assert len(lines) > 0
    assert any(line.startswith("data: ") for line in lines)
    # Check for end of stream
    assert any('data: [DONE]' in line for line in lines)

def test_text_completions_non_streaming():
    """Test non-streaming text completions endpoint."""
    data = {
        "model": "gpt-3.5-turbo-instruct",
        "prompt": "Hello, world!",
        "stream": False
    }
    headers = {"Authorization": "Bearer test_key"}

    response = client.post("/v1/completions", json=data, headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    json_response = response.json()
    assert "choices" in json_response

def test_invalid_api_key():
    """Test endpoint with invalid API key."""
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }
    headers = {"Authorization": "Bearer invalid_key"}

    response = client.post("/v1/chat/completions", json=data, headers=headers, stream=True)
    assert response.status_code == 401