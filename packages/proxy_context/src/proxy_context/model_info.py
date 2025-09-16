"""Model information data structures."""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class ModelInfo(BaseModel):
    """Information about a model."""

    id: str
    object: str = "model"
    created: int
    owned_by: str
    context_length: Optional[int] = None
    max_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Create from dictionary."""
        return cls(**data)
