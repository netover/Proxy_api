"""
Unit tests for model definitions.
"""

import pytest
from src.models.model_info import ModelInfo
from src.models.requests import ChatCompletionRequest, EmbeddingRequest
from src.models.responses import ChatCompletionResponse


class TestModelInfo:
    """Test ModelInfo model."""

    def test_model_info_creation(self):
        """Test ModelInfo creation."""
        model = ModelInfo(
            id="gpt-3.5-turbo",
            created=1677610602,
            owned_by="openai",
            permissions=[{"id": "perm1", "object": "model_permission"}]
        )

        assert model.id == "gpt-3.5-turbo"
        assert model.created == 1677610602
        assert model.owned_by == "openai"
        assert len(model.permissions) == 1

    def test_model_info_validation(self):
        """Test ModelInfo validation."""
        # Valid model
        model = ModelInfo(
            id="gpt-4",
            created=1677610602,
            owned_by="openai"
        )
        assert model.id == "gpt-4"

        # Test invalid object type
        with pytest.raises(ValueError):
            ModelInfo(
                id="test",
                created=1677610602,
                owned_by="openai",
                object="invalid_type"
            )

    def test_model_info_dict_conversion(self):
        """Test ModelInfo to/from dict conversion."""
        original = ModelInfo(
            id="test-model",
            created=1677610602,
            owned_by="test-owner",
            permissions=[{"id": "perm1", "object": "model_permission"}]
        )

        # Test to_dict
        data = original.to_dict()
        assert data["id"] == "test-model"
        assert data["created"] == 1677610602
        assert data["owned_by"] == "test-owner"

        # Test from_dict
        reconstructed = ModelInfo.from_dict(data)
        assert reconstructed.id == original.id
        assert reconstructed.created == original.created


class TestChatCompletionRequest:
    """Test ChatCompletionRequest model."""

    def test_chat_completion_request_creation(self):
        """Test ChatCompletionRequest creation."""
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=100
        )

        assert request.model == "gpt-3.5-turbo"
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"
        assert request.max_tokens == 100

    def test_chat_completion_request_validation(self):
        """Test ChatCompletionRequest validation."""
        # Valid request
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )
        assert request.model == "gpt-3.5-turbo"

    def test_chat_completion_request_dict_methods(self):
        """Test ChatCompletionRequest dict methods."""
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )

        # Test model_dump
        data = request.model_dump()
        assert data["model"] == "gpt-3.5-turbo"
        assert "messages" in data


class TestEmbeddingRequest:
    """Test EmbeddingRequest model."""

    def test_embedding_request_creation(self):
        """Test EmbeddingRequest creation."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test input for embedding"
        )

        assert request.model == "text-embedding-ada-002"
        assert request.input == "Test input for embedding"

    def test_embedding_request_with_list_input(self):
        """Test EmbeddingRequest with list input."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input=["Text 1", "Text 2", "Text 3"]
        )

        assert request.model == "text-embedding-ada-002"
        assert isinstance(request.input, list)
        assert len(request.input) == 3

    def test_embedding_request_dict_methods(self):
        """Test EmbeddingRequest dict methods."""
        request = EmbeddingRequest(
            model="text-embedding-ada-002",
            input="Test input"
        )

        data = request.model_dump()
        assert data["model"] == "text-embedding-ada-002"
        assert data["input"] == "Test input"


class TestChatCompletionResponse:
    """Test ChatCompletionResponse model."""

    def test_chat_completion_response_creation(self):
        """Test ChatCompletionResponse creation."""
        response = ChatCompletionResponse(
            id="chatcmpl-123",
            object="chat.completion",
            created=1677652288,
            model="gpt-3.5-turbo",
            choices=[
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Hello! How can I help you?"
                    },
                    "finish_reason": "stop"
                }
            ],
            usage={
                "prompt_tokens": 9,
                "completion_tokens": 12,
                "total_tokens": 21
            }
        )

        assert response.id == "chatcmpl-123"
        assert response.model == "gpt-3.5-turbo"
        assert len(response.choices) == 1
        assert response.usage["total_tokens"] == 21

    def test_chat_completion_response_dict_conversion(self):
        """Test ChatCompletionResponse dict conversion."""
        response = ChatCompletionResponse(
            id="test-response",
            object="chat.completion",
            created=1677652288,
            model="gpt-3.5-turbo",
            choices=[],
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )

        data = response.model_dump()
        assert data["id"] == "test-response"
        assert data["object"] == "chat.completion"
        assert data["model"] == "gpt-3.5-turbo"
