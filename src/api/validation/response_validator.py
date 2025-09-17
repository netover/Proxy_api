"""
Response validation and formatting layer for API endpoints.

This module provides centralized response validation, formatting,
and sanitization for all outgoing API responses.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ResponseValidator:
    """Centralized response validation and formatting."""

    def __init__(self):
        self.max_response_size = 10 * 1024 * 1024  # 10MB max response size
        self.sensitive_fields = [
            "api_key",
            "secret",
            "password",
            "token",
            "key",
        ]

    async def validate_chat_completion_response(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and format chat completion response."""
        try:
            # Ensure required fields are present
            required_fields = ["id", "object", "created", "model", "choices"]
            for field in required_fields:
                if field not in response:
                    logger.warning(f"Missing required field in chat response: {field}")
                    response[field] = self._get_default_value(field)

            # Validate choices structure
            if "choices" in response:
                choices = response["choices"]
                if not isinstance(choices, list):
                    logger.warning("Choices is not a list, converting")
                    response["choices"] = [choices] if choices else []

                # Validate each choice
                validated_choices = []
                for i, choice in enumerate(response["choices"]):
                    if not isinstance(choice, dict):
                        logger.warning(f"Choice {i} is not a dict, skipping")
                        continue

                    validated_choice = {
                        "index": choice.get("index", i),
                        "message": {
                            "role": choice.get("message", {}).get("role", "assistant"),
                            "content": choice.get("message", {}).get("content", ""),
                        },
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                    validated_choices.append(validated_choice)

                response["choices"] = validated_choices

            # Sanitize sensitive data
            response = self._sanitize_response(response)

            # Validate response size
            response_size = len(json.dumps(response).encode("utf-8"))
            if response_size > self.max_response_size:
                logger.warning(f"Response size too large: {response_size} bytes")
                # Truncate if necessary
                response = self._truncate_large_response(response)

            return response

        except Exception as e:
            logger.error(f"Error validating chat completion response: {e}")
            return self._create_error_response("Response validation failed", str(e))

    async def validate_text_completion_response(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and format text completion response."""
        try:
            # Ensure required fields
            required_fields = ["id", "object", "created", "model", "choices"]
            for field in required_fields:
                if field not in response:
                    response[field] = self._get_default_value(field)

            # Validate choices
            if "choices" in response:
                choices = response["choices"]
                if not isinstance(choices, list):
                    response["choices"] = [choices] if choices else []

                validated_choices = []
                for i, choice in enumerate(response["choices"]):
                    if not isinstance(choice, dict):
                        continue

                    validated_choice = {
                        "text": choice.get("text", ""),
                        "index": choice.get("index", i),
                        "finish_reason": choice.get("finish_reason", "stop"),
                    }
                    validated_choices.append(validated_choice)

                response["choices"] = validated_choices

            # Sanitize and validate size
            response = self._sanitize_response(response)
            response = self._validate_response_size(response)

            return response

        except Exception as e:
            logger.error(f"Error validating text completion response: {e}")
            return self._create_error_response("Response validation failed", str(e))

    async def validate_embedding_response(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and format embedding response."""
        try:
            # Ensure required fields
            required_fields = ["object", "data", "model", "usage"]
            for field in required_fields:
                if field not in response:
                    response[field] = self._get_default_value(field)

            # Validate data array
            if "data" in response:
                data = response["data"]
                if not isinstance(data, list):
                    response["data"] = []

                # Validate embedding objects
                validated_data = []
                for i, item in enumerate(data):
                    if not isinstance(item, dict):
                        continue

                    validated_item = {
                        "object": "embedding",
                        "embedding": item.get("embedding", []),
                        "index": item.get("index", i),
                    }
                    validated_data.append(validated_item)

                response["data"] = validated_data

            # Sanitize and validate
            response = self._sanitize_response(response)
            response = self._validate_response_size(response)

            return response

        except Exception as e:
            logger.error(f"Error validating embedding response: {e}")
            return self._create_error_response("Response validation failed", str(e))

    async def validate_image_generation_response(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and format image generation response."""
        try:
            # Ensure required fields
            required_fields = ["created", "data"]
            for field in required_fields:
                if field not in response:
                    response[field] = self._get_default_value(field)

            # Validate data array
            if "data" in response:
                data = response["data"]
                if not isinstance(data, list):
                    response["data"] = []

                # Validate image objects
                validated_data = []
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    validated_item = {
                        "url": item.get("url", ""),
                        "revised_prompt": item.get("revised_prompt", ""),
                    }
                    validated_data.append(validated_item)

                response["data"] = validated_data

            # Sanitize and validate
            response = self._sanitize_response(response)
            response = self._validate_response_size(response)

            return response

        except Exception as e:
            logger.error(f"Error validating image response: {e}")
            return self._create_error_response("Response validation failed", str(e))

    async def validate_generic_response(
        self, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and format generic API response."""
        try:
            # Basic sanitization and size validation
            response = self._sanitize_response(response)
            response = self._validate_response_size(response)

            # Add timestamp if not present
            if "timestamp" not in response:
                response["timestamp"] = int(datetime.now().timestamp())

            return response

        except Exception as e:
            logger.error(f"Error validating generic response: {e}")
            return self._create_error_response("Response validation failed", str(e))

    def _sanitize_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or mask sensitive information from response."""

        def sanitize_value(value: Any) -> Any:
            if isinstance(value, dict):
                return {
                    k: sanitize_value(v)
                    for k, v in value.items()
                    if k.lower() not in self.sensitive_fields
                }
            elif isinstance(value, list):
                return [sanitize_value(item) for item in value]
            else:
                return value

        return sanitize_value(response)

    def _validate_response_size(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and potentially truncate response based on size."""
        response_str = json.dumps(response)
        response_size = len(response_str.encode("utf-8"))

        if response_size > self.max_response_size:
            logger.warning(
                f"Response size {response_size} exceeds limit {self.max_response_size}"
            )

            # Try to truncate large text fields
            if "choices" in response:
                for choice in response["choices"]:
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        if len(content) > 10000:  # Arbitrary large content limit
                            choice["message"]["content"] = (
                                content[:10000] + "...[truncated]"
                            )

            # Recalculate size after truncation
            response_str = json.dumps(response)
            response_size = len(response_str.encode("utf-8"))

            if response_size > self.max_response_size:
                logger.error(
                    f"Response still too large after truncation: {response_size}"
                )
                return self._create_error_response(
                    "Response too large",
                    "Response exceeded maximum size limit",
                )

        return response

    def _truncate_large_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Truncate response to fit size limits."""
        # Simple truncation strategy - keep essential fields only
        truncated = {
            "id": response.get("id", "truncated"),
            "object": response.get("object", "error"),
            "created": response.get("created", int(datetime.now().timestamp())),
            "model": response.get("model", "unknown"),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Response was truncated due to size limits",
                    },
                    "finish_reason": "length",
                }
            ],
        }
        return truncated

    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing required fields."""
        defaults = {
            "id": f"response_{int(datetime.now().timestamp())}",
            "object": "response",
            "created": int(datetime.now().timestamp()),
            "model": "unknown",
            "choices": [],
            "data": [],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        }
        return defaults.get(field, None)

    def _create_error_response(self, error_type: str, message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": {
                "type": error_type,
                "message": message,
                "timestamp": int(datetime.now().timestamp()),
            }
        }


# Global validator instance
response_validator = ResponseValidator()
