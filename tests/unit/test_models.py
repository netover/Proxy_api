import pytest
from src.models.requests import ModelSelectionRequest
from src.models.model_info import ModelInfoExtended

def test_model_selection_request_validation():
    """Test ModelSelectionRequest validation."""
    # Valid request
    valid_request = ModelSelectionRequest(
        selected_model="gpt-4",
        editable=True,
        priority=5,
        max_tokens=1000,
        temperature=0.8,
    )
    assert valid_request.selected_model == "gpt-4"
    assert valid_request.editable is True
    assert valid_request.priority == 5

    # Test whitespace trimming
    request_with_whitespace = ModelSelectionRequest(
        selected_model="  gpt-4  ", editable=True
    )
    assert request_with_whitespace.selected_model == "gpt-4"

    # Test invalid priority
    with pytest.raises(ValueError):
        ModelSelectionRequest(
            selected_model="gpt-4",
            editable=True,
            priority=15,  # Out of range
        )

    # Test empty model ID
    with pytest.raises(ValueError):
        ModelSelectionRequest(selected_model="   ", editable=True)

def test_model_info_extended_creation():
    """Test ModelInfoExtended model creation."""
    model = ModelInfoExtended(
        id="gpt-4",
        created=1677649200,
        owned_by="openai",
        provider="openai",
        status="active",
        capabilities=["text_generation", "chat"],
        context_window=8192,
        max_tokens=4096,
        pricing={"input": 0.03, "output": 0.06},
        description="GPT-4 language model",
        version="2023-03-15",
    )

    assert model.id == "gpt-4"
    assert model.provider == "openai"
    assert "text_generation" in model.capabilities
    assert model.context_window == 8192
