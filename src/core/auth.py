"""
Authentication middleware for LLM Proxy API
Provides API key and JWT token-based authentication
"""

from fastapi import Request, HTTPException, Depends
from typing import Any
import hashlib
import secrets
from src.core.config import settings
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class APIKeyAuth:
    """API Key authentication"""
    
    def __init__(self, api_keys: list[str]):
        self.valid_api_key_hashes = self._load_api_keys(api_keys)
    
    def _load_api_keys(self, api_keys: list[str]) -> set[str]:
        """Load and hash API keys"""
        hashed_keys = set()
        for key in api_keys:
            if key:
                hashed_keys.add(hashlib.sha256(key.encode()).hexdigest())
        
        logger.info(f"Loaded {len(hashed_keys)} API keys for authentication")
        return hashed_keys
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key securely"""
        if not api_key or not self.valid_api_key_hashes:
            return False
        
        # Hash the provided key to compare with the stored hashes
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Securely compare the hash against all valid hashes
        # This is important to prevent timing attacks.
        is_valid = False
        for valid_hash in self.valid_api_key_hashes:
            secrets.compare_digest(key_hash, valid_hash)
            if key_hash == valid_hash:
                is_valid = True
                break

        return is_valid

# This dependency will be initialized during app startup
def get_api_key_auth(request: Request) -> APIKeyAuth:
    return request.app.state.api_key_auth

async def verify_api_key(
    request: Request,
    api_key_auth: APIKeyAuth = Depends(get_api_key_auth)
) -> bool:
    """Verify API key from request headers using the application's auth instance"""
    # Check for API key in custom header or Authorization header
    api_key = request.headers.get(settings.api_key_header.lower())
    if not api_key:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
    
    if not api_key:
        logger.warning("No API key provided", path=request.url.path)
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    if not api_key_auth.verify_api_key(api_key):
        logger.warning("Invalid API key provided", path=request.url.path)
        raise HTTPException(
            status_code=401,
            detail="Invalid or unauthorized API key"
        )
    
    logger.info("API key verified successfully", path=request.url.path)
    return True
