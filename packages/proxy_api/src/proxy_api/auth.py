"""Authentication utilities for proxy_api package."""

from typing import Optional
import os


def verify_api_key(api_key: Optional[str] = None) -> bool:
    """Verify API key (placeholder implementation)."""
    # In a real implementation, this would validate against a database or cache
    expected_key = os.getenv("API_KEY", "test-key")
    return api_key == expected_key


async def get_api_key_from_request(request) -> Optional[str]:
    """Extract API key from request headers."""
    return request.headers.get("Authorization", "").replace("Bearer ", "")