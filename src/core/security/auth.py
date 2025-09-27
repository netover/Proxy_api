from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from typing import List, Set

# Define the header to look for the API key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class APIKeyAuth:
    """
    A simple class to manage and verify API keys.
    """
    def __init__(self, valid_keys: List[str]):
        """
        Initializes the auth manager with a list of valid keys.
        It automatically trims whitespace from the keys.
        Args:
            valid_keys: A list of strings representing the allowed API keys.
        """
        self.valid_keys: Set[str] = {key.strip() for key in valid_keys if key and key.strip()}

    def verify(self, api_key: str) -> bool:
        """
        Verifies if a given API key is in the set of valid keys.
        """
        if not api_key:
            return False
        return api_key in self.valid_keys

def get_api_key_dependency(
    api_key: str = Security(api_key_header),
) -> str:
    """
    FastAPI dependency to verify the API key from the request header.

    This function will be used in route definitions to protect endpoints.
    It relies on the 'api_key_auth' object being available in the app state.

    Usage in a route:
    app.get("/secure", dependencies=[Depends(get_api_key)])
    """
    # This dependency function itself doesn't have access to app.state at definition time.
    # The verification logic will need to be a separate dependency that gets the app state.
    # For now, let's just return the key and assume another dependency will validate.
    # This is a placeholder for a more complete implementation.

    # A more complete implementation would look like this inside the endpoint:
    # from fastapi import Depends, Request
    # def my_endpoint(request: Request, api_key: str = Security(api_key_header)):
    #   if not request.app.state.app_state.api_key_auth.verify(api_key):
    #     raise HTTPException(...)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated"
        )
    return api_key

# This is a better dependency that can be used directly
from fastapi import Request

async def verify_api_key(request: Request, api_key: str = Security(api_key_header)):
    """
    A dependency that can be used in FastAPI routes to verify an API key.
    It retrieves the APIKeyAuth instance from the application state.
    """
    auth_manager = request.app.state.app_state.api_key_auth
    if not auth_manager:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system not configured",
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authenticated",
        )

    if not auth_manager.verify(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
