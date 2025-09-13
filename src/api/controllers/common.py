import re
import time
import uuid
from http import HTTPStatus
from typing import Any, AsyncGenerator, Dict, List, Union

from fastapi import BackgroundTasks, Request
from fastapi.responses import JSONResponse

from src.api.controllers.context_controller import background_condense
from src.core.circuit_breaker import get_circuit_breaker
from src.core.exceptions import (InvalidRequestError, NotImplementedError,
                                 ServiceUnavailableError)
from src.core.logging import ContextualLogger
from src.core.metrics import metrics_collector
from src.models.requests import (ChatCompletionRequest, EmbeddingRequest,
                                 TextCompletionRequest)
from src.utils.tasks import safe_background_task

logger = ContextualLogger(__name__)

class RequestRouter:
    """Centralized request routing with intelligent fallback"""

    def __init__(self):
        self.circuit_breakers = {}

    async def route_request(self,
                          request: Request,
                          request_data: Union[ChatCompletionRequest, TextCompletionRequest, EmbeddingRequest, Dict[str, Any]],
                          operation: str,
                          background_tasks: BackgroundTasks) -> Union[Dict[str, Any], AsyncGenerator]:
        """
        Generic request router with comprehensive error handling and fallback
        """
        app_state = request.app.state.app_state
        request_id = f"{operation}_{int(time.time() * 1000)}"
        logger.set_context(request_id=request_id, operation=operation, model=request_data.get('model', 'unknown'))

        # Get providers for the model
        model = request_data.get('model', '')
        providers = await app_state.provider_factory.get_providers_for_model(model)

        if not providers:
            logger.error("No providers available for model", model=model)
            raise InvalidRequestError(
                f"Model '{model}' is not supported by any available provider",
                param="model",
                code="model_not_found"
            )

        # Check for forced provider
        config = app_state.config_manager.load_config()
        forced_provider = config.get_forced_provider()

        if forced_provider and forced_provider.name in [p.name for p in providers]:
            # Use forced provider exclusively
            providers = [p for p in providers if p.name == forced_provider.name]
            logger.info(f"Using forced provider: {forced_provider.name}")

        # Track attempts for metrics
        attempt_info = []
        last_exception = None

        # Try providers in priority order
        for i, provider in enumerate(providers):
            attempt_start = time.time()

            try:
                logger.info(f"Attempting {operation} with provider {provider.name} (attempt {i+1}/{len(providers)})")

                circuit_breaker = get_circuit_breaker(f"provider_{provider.name}")

                # Choose the appropriate method based on operation
                if operation == "chat_completion":
                    method = provider.create_completion
                elif operation == "text_completion":
                    method = provider.create_text_completion
                elif operation == "embeddings":
                    method = provider.create_embeddings
                elif operation == "image_generation":
                    method = provider.create_image
                else:
                    raise ValueError(f"Unknown operation: {operation}")

                req_dict = request_data.dict(exclude_unset=True) if hasattr(request_data, 'dict') else request_data
                result = await circuit_breaker.execute(lambda: method(req_dict))

                attempt_time = time.time() - attempt_start

                # Record successful attempt
                attempt_info.append({
                    "provider": provider.name,
                    "success": True,
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })

                # Log success and record metrics
                logger.info(f"{operation} successful",
                          provider=provider.name,
                          response_time=attempt_time,
                          total_attempts=i + 1)

                # Background task to record detailed metrics
                background_tasks.add_task(
                    self._record_success_metrics,
                    request_id, operation, provider.name, attempt_time, attempt_info
                )

                # Add provider info to response
                if isinstance(result, dict):
                    result.setdefault("_proxy_info", {}).update({
                        "provider": provider.name,
                        "attempt_number": i + 1,
                        "response_time": attempt_time,
                        "request_id": request_id
                    })

                return result

            except NotImplementedError:
                # Provider doesn't support this operation
                attempt_time = time.time() - attempt_start
                attempt_info.append({
                    "provider": provider.name,
                    "success": False,
                    "error": "operation_not_supported",
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })

                logger.info(f"Provider {provider.name} doesn't support {operation}, trying next")
                continue

            except Exception as e:
                attempt_time = time.time() - attempt_start
                last_exception = e

                # Record failed attempt
                attempt_info.append({
                    "provider": provider.name,
                    "success": False,
                    "error": type(e).__name__,
                    "error_message": str(e),
                    "response_time": attempt_time,
                    "attempt_number": i + 1
                })

                logger.error(f"Provider {provider.name} failed for {operation}",
                            error=str(e),
                            error_type=type(e).__name__,
                            response_time=attempt_time)

                # Handle context length errors
                msg = str(e)
                config = request.app.state.app_state.config
                if any(re.search(pattern, msg, re.IGNORECASE) for pattern in config.settings.condensation.error_patterns):
                    if not req_dict.get("stream", False):
                        request_id = str(uuid.uuid4())
                        chunks = [m["content"] for m in req_dict.get("messages", [])]
                        background_tasks.add_task(safe_background_task(background_condense), request_id, request, chunks)

                        return JSONResponse(
                            status_code=HTTPStatus.ACCEPTED,
                            content={
                                "status": "processing",
                                "request_id": request_id,
                                "message": f"Context error detected; summarization in progress. Poll /summary/{request_id} for result.",
                                "estimated_time": "5-10 seconds"
                            }
                        )
                    # Truncate for streaming
                    req_dict["messages"] = req_dict["messages"][-len(req_dict["messages"])//2:]
                    req_dict["stream"] = False
                    # Re-attempt with the same provider
                    # This is a bit tricky, maybe just continue to the next provider is better.
                    # For now, let's just log it and continue.
                    logger.warning(f"Truncating context for streaming request and retrying with next provider.")

                # Continue to next provider
                continue

        # All providers failed
        logger.error(f"All providers failed for {operation}",
                    total_providers=len(providers),
                    attempts=len(attempt_info))

        # Background task to record failure metrics
        background_tasks.add_task(
            self._record_failure_metrics,
            request_id, operation, attempt_info
        )

        # Determine appropriate error response
        if all(attempt["error"] == "operation_not_supported" for attempt in attempt_info):
            raise NotImplementedError(
                f"The {operation} operation is not supported by any provider for model '{model}'",
                code="operation_not_supported"
            )
        else:
            errors = [
                {
                    "provider": attempt["provider"],
                    "error_type": attempt["error"],
                    "error_message": attempt.get("error_message", "Unknown error")
                }
                for attempt in attempt_info if not attempt["success"]
            ]
            raise ServiceUnavailableError(
                "All providers are currently unavailable",
                code="providers_unavailable"
            )

    async def _record_success_metrics(self, request_id: str, operation: str,
                                    provider_name: str, response_time: float,
                                    attempt_info: List[Dict]) -> None:
        """Background task to record detailed success metrics"""
        try:
            metrics_collector.record_request(
                provider_name,
                success=True,
                response_time=response_time,
                operation=operation,
                attempts=len(attempt_info)
            )
        except Exception as e:
            logger.error(f"Failed to record success metrics: {e}")

    async def _record_failure_metrics(self, request_id: str, operation: str,
                                    attempt_info: List[Dict]) -> None:
        """Background task to record detailed failure metrics"""
        try:
            for attempt in attempt_info:
                if not attempt["success"]:
                    metrics_collector.record_request(
                        attempt["provider"],
                        success=False,
                        response_time=attempt["response_time"],
                        error_type=attempt.get("error", "unknown"),
                        operation=operation
                    )
        except Exception as e:
            logger.error(f"Failed to record failure metrics: {e}")

# Global router instance
request_router = RequestRouter()