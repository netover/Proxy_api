import time

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse

from src.core.auth import verify_api_key
from src.core.logging import ContextualLogger
from src.core.rate_limiter import rate_limiter
from src.models.requests import ChatCompletionRequest, TextCompletionRequest

from .common import request_router  # Import shared router

logger = ContextualLogger(__name__)

router = APIRouter()

@router.post("/v1/chat/completions")
@rate_limiter.limit("100/minute")
async def chat_completions(
    request: Request,
    completion_request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible chat completions endpoint"""
    start_time = time.time()
    model = completion_request.model
    stream = completion_request.stream

    logger.info("Chat completion request started",
               model=model,
               stream=stream,
               message_count=len(completion_request.messages) if hasattr(completion_request, 'messages') else 0)

    result = await request_router.route_request(
        request,
        completion_request,
        "chat_completion",
        background_tasks
    )

    response_time = time.time() - start_time
    logger.info("Chat completion request completed",
               model=model,
               stream=stream,
               response_time=response_time)

    if completion_request.stream:
        return StreamingResponse(result, media_type="text/event-stream")
    return result

@router.post("/v1/completions")
@rate_limiter.limit("100/minute")
async def text_completions(
    request: Request,
    completion_request: TextCompletionRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_api_key)
):
    """OpenAI-compatible text completions endpoint"""
    start_time = time.time()
    model = completion_request.model
    stream = completion_request.stream

    logger.info("Text completion request started",
               model=model,
               stream=stream,
               prompt_length=len(completion_request.prompt) if hasattr(completion_request, 'prompt') else 0)

    result = await request_router.route_request(
        request,
        completion_request,
        "text_completion",
        background_tasks
    )

    response_time = time.time() - start_time
    logger.info("Text completion request completed",
               model=model,
               stream=stream,
               response_time=response_time)

    if completion_request.stream:
        return StreamingResponse(result, media_type="text/event-stream")
    return result