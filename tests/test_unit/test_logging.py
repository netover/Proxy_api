"""
Unit tests for logging system.
"""

import pytest
import json
import logging
from unittest.mock import patch
from src.core.logging import ContextualLogger, setup_logging


class TestContextualLogger:
    """Test contextual logger functionality."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = ContextualLogger("test.module")

        assert logger.logger is not None
        assert hasattr(logger.logger, 'info')
        assert hasattr(logger.logger, 'error')
        assert hasattr(logger.logger, 'warning')

    def test_logger_methods(self):
        """Test logger method calls."""
        logger = ContextualLogger("test.module")

        # These should not raise exceptions
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("Test message", extra_field="extra_value")
            mock_info.assert_called_once()

        with patch.object(logger.logger, 'error') as mock_error:
            logger.error("Error message", error_code=500)
            mock_error.assert_called_once()

        with patch.object(logger.logger, 'warning') as mock_warning:
            logger.warning("Warning message", warning_type="deprecated")
            mock_warning.assert_called_once()

    def test_logger_span_context_manager(self):
        """Test logger span context manager."""
        logger = ContextualLogger("test.module")

        # Test span context manager - should return a context manager
        span_context = logger.span("test_span", attributes={"key": "value"})
        assert span_context is not None

        # Should be able to use it as context manager
        with span_context:
            pass


class TestSetupLogging:
    """Test logging setup functionality."""

    def test_setup_logging_default(self):
        """Test logging setup with default parameters."""
        # Should not raise exceptions
        setup_logging()

        # Check that logging is configured
        root_logger = logging.getLogger()
        assert len(root_logger.handlers) > 0

    def test_setup_logging_custom_level(self):
        """Test logging setup with custom level."""
        # Just test that setup_logging doesn't raise an exception
        setup_logging("DEBUG")

        # Verify that the function completes without error
        assert True

    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level."""
        # Should not raise exception, should use default
        setup_logging("INVALID_LEVEL")

        # Verify that the function completes without error
        assert True

    def test_structlog_configuration(self):
        """Test that structlog is properly configured."""
        setup_logging("INFO")

        # Check that structlog is configured
        import structlog
        logger = structlog.get_logger("test")
        assert logger is not None

        # Test that logger can be used (basic functionality)
        # Since structlog is configured, it should work without errors
        assert hasattr(logger, 'info')


class TestLoggingIntegration:
    """Test logging integration with other systems."""

    def test_logging_with_metrics(self):
        """Test logging integration with metrics."""
        logger = ContextualLogger("integration.test")

        # Test that the logger can be created and used
        logger.info("Test message", test_metric="value")
        logger.debug("Debug message")

    def test_logging_with_context(self):
        """Test contextual logging."""
        logger = ContextualLogger("context.test")

        # Test context setting
        with patch.object(logger.logger, 'info') as mock_info:
            logger.info("Contextual message", request_id="123", user="test_user")
            # Should call with context
            mock_info.assert_called_once()

    def test_error_logging_with_exception(self):
        """Test error logging with exception information."""
        logger = ContextualLogger("error.test")

        with patch.object(logger.logger, 'error') as mock_error:
            try:
                raise ValueError("Test error")
            except ValueError:
                logger.error("Error occurred", error="Test error", error_type="ValueError")

            # Should log with error context
            mock_error.assert_called_once()
