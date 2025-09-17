from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    code: str
    message: str
    target: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
