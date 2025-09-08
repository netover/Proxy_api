"""
Authentication middleware for LLM Proxy API
Provides API key and JWT token-based authentication
"""

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import os
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
from src.core.config import settings
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

# In-memory storage for API keys (in production, use a database)
API_KEYS = {}
VALID_API_KEYS = set()

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

class APIKeyAuth:
    """API Key authentication"""
    
    def __init__(self):
        self.load_api_keys()
    
    def load_api_keys(self):
        """Load API keys from environment variables"""
        # Load OpenAI API key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            key_hash = hashlib.sha256(openai_key.encode()).hexdigest()
            API_KEYS[key_hash] = {"provider": "openai", "created_at": datetime.now()}
            VALID_API_KEYS.add(key_hash)
        
        # Load Anthropic API key
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            key_hash = hashlib.sha256(anthropic_key.encode()).hexdigest()
            API_KEYS[key_hash] = {"provider": "anthropic", "created_at": datetime.now()}
            VALID_API_KEYS.add(key_hash)
        
        logger.info(f"Loaded {len(VALID_API_KEYS)} API keys")
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify API key"""
        if not api_key:
            return False
        
        # Hash the API key for comparison
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return key_hash in VALID_API_KEYS

class JWTAuth:
    """JWT token authentication"""
    
    @staticmethod
    def create_token(user_id: str, scopes: list = None) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "scopes": scopes or [],
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired JWT token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid JWT token")
            return None

# Authentication instances
api_key_auth = APIKeyAuth()
jwt_auth = JWTAuth()
security = HTTPBearer()

async def verify_api_key(request: Request) -> bool:
    """Verify API key from request headers"""
    # Check for API key in custom header
    api_key = request.headers.get(settings.api_key_header.lower(), None)
    
    # If not found, check Authorization header for Bearer token
    if not api_key:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]  # Remove "Bearer " prefix
    
    if not api_key:
        logger.warning("No API key provided", path=request.url.path)
        raise HTTPException(
            status_code=401,
            detail="API key required"
        )
    
    if not api_key_auth.verify_api_key(api_key):
        logger.warning("Invalid API key", path=request.url.path)
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    logger.info("API key verified", path=request.url.path)
    return True

async def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token"""
    token = credentials.credentials
    payload = jwt_auth.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    
    logger.info("JWT token verified", user_id=payload.get("user_id"))
    return payload

# Rate limiting per API key
API_KEY_REQUEST_COUNT = {}
API_KEY_RATE_LIMIT = 100  # requests per window
API_KEY_RATE_WINDOW = 3600  # 1 hour in seconds

async def check_rate_limit(request: Request) -> bool:
    """Check rate limit per API key"""
    # Get API key from request
    api_key = request.headers.get(settings.api_key_header.lower(), None)
    
    if not api_key:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]
    
    if not api_key:
        # Use IP-based rate limiting if no API key
        client_ip = request.client.host
        key = f"ip:{client_ip}"
    else:
        # Use API key-based rate limiting
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key = f"key:{key_hash}"
    
    # Check rate limit
    now = datetime.now().timestamp()
    if key not in API_KEY_REQUEST_COUNT:
        API_KEY_REQUEST_COUNT[key] = []
    
    # Remove old requests outside the window
    API_KEY_REQUEST_COUNT[key] = [
        timestamp for timestamp in API_KEY_REQUEST_COUNT[key]
        if now - timestamp < API_KEY_RATE_WINDOW
    ]
    
    # Check if limit exceeded
    if len(API_KEY_REQUEST_COUNT[key]) >= API_KEY_RATE_LIMIT:
        logger.warning("Rate limit exceeded", key=key)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    # Add current request
    API_KEY_REQUEST_COUNT[key].append(now)
    
    return True
