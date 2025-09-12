"""
Request validation and sanitization layer for API endpoints.

This module provides centralized request validation, sanitization,
and security checks for all incoming API requests.
"""

import logging
import re
from typing import Any, Dict

from src.core.exceptions import InvalidRequestError
from src.api.errors.error_handlers import error_handler

logger = logging.getLogger(__name__)

class RequestValidator:
    """Centralized request validation and sanitization."""

    # Security patterns
    SQL_INJECTION_PATTERNS = [
        r';\s*--',  # SQL comment
        r';\s*/\*',  # SQL block comment
        r'union\s+select',  # Union-based injection
        r'\b(drop|delete|update|insert)\b.*\binto\b',  # DML operations
    ]

    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers
        r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
    ]

    def __init__(self):
        self.max_prompt_length = 100000  # Max characters for prompts
        self.max_model_name_length = 100  # Max length for model names
        self.allowed_model_pattern = re.compile(r'^[a-zA-Z0-9\-_\.]+$')

    async def validate_chat_completion_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize chat completion request."""
        try:
            # Validate model name
            model = request_data.get('model', '')
            if not model:
                raise InvalidRequestError("Model name is required", param="model")

            if not self._is_valid_model_name(model):
                raise InvalidRequestError(
                    f"Invalid model name format: {model}",
                    param="model",
                    code="invalid_model_name"
                )

            # Validate messages
            messages = request_data.get('messages', [])
            if not messages:
                raise InvalidRequestError("Messages array is required", param="messages")

            if not isinstance(messages, list) or len(messages) == 0:
                raise InvalidRequestError("Messages must be a non-empty array", param="messages")

            # Sanitize messages
            sanitized_messages = []
            for i, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    raise InvalidRequestError(f"Message {i} must be an object", param=f"messages[{i}]")

                role = msg.get('role')
                content = msg.get('content')

                if not role or role not in ['system', 'user', 'assistant']:
                    raise InvalidRequestError(
                        f"Invalid role '{role}' in message {i}",
                        param=f"messages[{i}].role"
                    )

                if not content:
                    raise InvalidRequestError(
                        f"Message {i} content is required",
                        param=f"messages[{i}].content"
                    )

                # Sanitize content
                sanitized_content = self._sanitize_text(content)
                sanitized_messages.append({
                    'role': role,
                    'content': sanitized_content
                })

            # Validate and sanitize other parameters
            sanitized_request = request_data.copy()
            sanitized_request['messages'] = sanitized_messages

            # Validate temperature
            if 'temperature' in sanitized_request:
                temp = sanitized_request['temperature']
                if not isinstance(temp, (int, float)) or not (0 <= temp <= 2):
                    raise InvalidRequestError(
                        "Temperature must be between 0 and 2",
                        param="temperature"
                    )

            # Validate max_tokens
            if 'max_tokens' in sanitized_request:
                max_tokens = sanitized_request['max_tokens']
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    raise InvalidRequestError(
                        "max_tokens must be a positive integer",
                        param="max_tokens"
                    )

            return sanitized_request

        except InvalidRequestError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating chat request: {e}")
            sanitized_error = error_handler._sanitize_error_message(str(e))
            raise InvalidRequestError(f"Request validation failed: {sanitized_error}")

    async def validate_text_completion_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize text completion request."""
        try:
            # Similar validation as chat completion but for prompt
            prompt = request_data.get('prompt', '')
            if not prompt:
                raise InvalidRequestError("Prompt is required", param="prompt")

            if not isinstance(prompt, str):
                raise InvalidRequestError("Prompt must be a string", param="prompt")

            if len(prompt) > self.max_prompt_length:
                raise InvalidRequestError(
                    f"Prompt too long: {len(prompt)} characters (max {self.max_prompt_length})",
                    param="prompt"
                )

            # Sanitize prompt
            sanitized_prompt = self._sanitize_text(prompt)

            # Validate model
            model = request_data.get('model', '')
            if not self._is_valid_model_name(model):
                raise InvalidRequestError(
                    f"Invalid model name: {model}",
                    param="model"
                )

            sanitized_request = request_data.copy()
            sanitized_request['prompt'] = sanitized_prompt

            return sanitized_request

        except InvalidRequestError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating text request: {e}")
            sanitized_error = error_handler._sanitize_error_message(str(e))
            raise InvalidRequestError(f"Request validation failed: {sanitized_error}")

    async def validate_embedding_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize embedding request."""
        try:
            # Validate input text
            input_text = request_data.get('input', '')
            if not input_text:
                raise InvalidRequestError("Input text is required", param="input")

            if isinstance(input_text, list):
                # Multiple inputs
                if len(input_text) == 0:
                    raise InvalidRequestError("Input array cannot be empty", param="input")

                sanitized_inputs = []
                for i, text in enumerate(input_text):
                    if not isinstance(text, str):
                        raise InvalidRequestError(
                            f"Input {i} must be a string",
                            param=f"input[{i}]"
                        )
                    sanitized_inputs.append(self._sanitize_text(text))
            else:
                # Single input
                if not isinstance(input_text, str):
                    raise InvalidRequestError("Input must be a string or array", param="input")
                sanitized_inputs = self._sanitize_text(input_text)

            # Validate model
            model = request_data.get('model', '')
            if not self._is_valid_model_name(model):
                raise InvalidRequestError(f"Invalid model name: {model}", param="model")

            sanitized_request = request_data.copy()
            sanitized_request['input'] = sanitized_inputs

            return sanitized_request

        except InvalidRequestError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error validating embedding request: {e}")
            sanitized_error = error_handler._sanitize_error_message(str(e))
            raise InvalidRequestError(f"Request validation failed: {sanitized_error}")

    def _is_valid_model_name(self, model_name: str) -> bool:
        """Check if model name has valid format."""
        if not model_name or len(model_name) > self.max_model_name_length:
            return False
        return bool(self.allowed_model_pattern.match(model_name))

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content for security."""
        if not isinstance(text, str):
            return str(text)

        # Remove potential SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove potential XSS patterns
        for pattern in self.XSS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Trim whitespace
        text = text.strip()

        return text

    def _validate_common_parameters(self, request_data: Dict[str, Any]) -> None:
        """Validate common parameters across all request types."""
        # Check for suspicious parameters
        suspicious_params = ['eval', 'exec', 'system', 'import', '__']
        for param in suspicious_params:
            if param in str(request_data).lower():
                logger.warning(f"Suspicious parameter detected: {param}")

# Global validator instance
request_validator = RequestValidator()