"""Model information data structures for OpenAI-compatible API."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ModelInfo:
    """
    Model information structure matching OpenAI API format.

    This class represents a model's metadata as returned by OpenAI-compatible APIs.
    It includes all standard fields plus optional extensions for compatibility.

    Attributes:
        id: Unique identifier for the model (e.g., "gpt-4", "claude-3-opus-20240229")
        object: Always "model" for model objects
        created: Unix timestamp when the model was created
        owned_by: Organization that owns the model
        permissions: List of permission objects for the model
        root: Optional root model identifier for model variants
        parent: Optional parent model identifier for model derivatives

    Example:
        >>> model = ModelInfo(
        ...     id="gpt-4",
        ...     object="model",
        ...     created=1687882411,
        ...     owned_by="openai",
        ...     permissions=[{"id": "modelperm-abc123", "object": "model_permission"}],
        ...     root="gpt-4",
        ...     parent=None
        ... )
    """

    id: str
    created: int
    owned_by: str
    object: str = "model"
    permissions: List[Dict[str, Any]] = field(default_factory=list)
    root: Optional[str] = None
    parent: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the model info after initialization."""
        if self.object != "model":
            raise ValueError(f"object must be 'model', got '{self.object}'")

        if not self.id:
            raise ValueError("id cannot be empty")

        if not self.owned_by:
            raise ValueError("owned_by cannot be empty")

        if self.created <= 0:
            raise ValueError("created must be a positive Unix timestamp")

    def __post_init__(self) -> None:
        """Validate the model info after initialization."""
        if self.object != "model":
            raise ValueError(f"object must be 'model', got '{self.object}'")

        if not self.id:
            raise ValueError("id cannot be empty")

        if not self.owned_by:
            raise ValueError("owned_by cannot be empty")

        if self.created <= 0:
            raise ValueError("created must be a positive Unix timestamp")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """
        Create ModelInfo instance from dictionary.

        Args:
            data: Dictionary containing model information

        Returns:
            ModelInfo instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            return cls(
                id=data["id"],
                object=data.get("object", "model"),
                created=data["created"],
                owned_by=data["owned_by"],
                permissions=data.get("permissions", []),
                root=data.get("root"),
                parent=data.get("parent"),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ModelInfo instance to dictionary.

        Returns:
            Dictionary representation of the model info
        """
        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "owned_by": self.owned_by,
            "permissions": self.permissions,
            "root": self.root,
            "parent": self.parent,
        }

    @property
    def created_datetime(self) -> datetime:
        """
        Get creation time as datetime object.

        Returns:
            Datetime object representing the creation time
        """
        return datetime.fromtimestamp(self.created)

    def __str__(self) -> str:
        """String representation of the model."""
        return f"ModelInfo(id='{self.id}', owned_by='{self.owned_by}')"

    def __repr__(self) -> str:
        """Detailed string representation for debugging."""
        return (
            f"ModelInfo("
            f"id='{self.id}', "
            f"object='{self.object}', "
            f"created={self.created}, "
            f"owned_by='{self.owned_by}', "
            f"permissions={len(self.permissions)} items, "
            f"root={self.root}, "
            f"parent={self.parent}"
            f")"
        )
