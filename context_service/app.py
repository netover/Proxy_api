from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from .utils.context_condenser_impl import condense_context

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Context Condensation Service",
    description="Service for condensing text context using AI providers",
    version="1.0.0"
)

class CondenseRequest(BaseModel):
    chunks: List[str]
    max_tokens: int = 512

class CondenseResponse(BaseModel):
    summary: str

@app.post("/condense", response_model=CondenseResponse)
async def condense_context_endpoint(req: CondenseRequest):
    """
    Condense a list of text chunks into a summary.

    - **chunks**: List of text chunks to condense
    - **max_tokens**: Maximum number of tokens for the summary (default: 512)
    """
    try:
        logger.info(f"Received condensation request with {len(req.chunks)} chunks, max_tokens={req.max_tokens}")
        summary = await condense_context(req.chunks, req.max_tokens)
        logger.info("Condensation completed successfully")
        return CondenseResponse(summary=summary)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail=f"Condensation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "context-condensation"}

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Context Condensation Service",
        "version": "1.0.0",
        "description": "Condenses text context using AI providers with caching and fallback support"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)