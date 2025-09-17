"""
Tests for Jinja2 template system and validation.
"""

import pytest
from pathlib import Path

from src.core.template_manager import TemplateManager


class TestTemplateManager:
    """Test the template manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template_dir = str(Path(__file__).parent.parent / "templates")
        self.manager = TemplateManager(self.template_dir)

    def test_template_initialization(self):
        """Test template manager initialization."""
        assert self.manager.template_dir == self.template_dir
        assert self.manager.env is not None

    def test_available_templates(self):
        """Test that required templates are available."""
        templates = self.manager.get_template_stats()
        template_names = templates["available_templates"]

        assert "prompt_chat.j2" in template_names
        assert "prompt_text.j2" in template_names

    def test_render_chat_prompt(self):
        """Test chat prompt rendering."""
        context = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "system_message": "You are a helpful assistant",
        }

        result = self.manager.render_chat_prompt(context)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "User: Hello" in result
        assert "Assistant: Hi there!" in result
        assert "System: You are a helpful assistant" in result

    def test_render_text_prompt(self):
        """Test text prompt rendering."""
        context = {
            "prompt": "Explain quantum computing",
            "context": "Physics background",
            "instructions": "Use simple language",
        }

        result = self.manager.render_text_prompt(context)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Explain quantum computing" in result
        assert "Physics background" in result

    def test_template_validation_success(self):
        """Test successful template variable validation."""
        context = {
            "messages": [{"role": "user", "content": "test"}],
            "system_message": "test system",
        }

        is_valid = self.manager.validate_template_variables("prompt_chat.j2", context)
        assert is_valid is True

    def test_template_validation_missing_variables(self):
        """Test template validation with missing variables."""
        context = {"messages": [{"role": "user", "content": "test"}]}

        # Should still be valid as system_message is optional
        is_valid = self.manager.validate_template_variables("prompt_chat.j2", context)
        assert is_valid is True

    def test_empty_context_handling(self):
        """Test rendering with empty context."""
        context = {}

        chat_result = self.manager.render_chat_prompt(context)
        text_result = self.manager.render_text_prompt(context)

        assert isinstance(chat_result, str)
        assert isinstance(text_result, str)

    def test_complex_context_rendering(self):
        """Test rendering with complex context."""
        context = {
            "messages": [
                {"role": "system", "content": "You are an AI assistant"},
                {"role": "user", "content": "What is AI?"},
                {"role": "assistant", "content": "AI is..."},
                {"role": "user", "content": "Explain ML vs DL"},
            ],
            "system_message": "Focus on clarity",
            "include_examples": True,
            "examples": [
                {"role": "user", "content": "Example 1"},
                {"role": "assistant", "content": "Example response 1"},
            ],
            "instructions": "Be concise and accurate",
            "include_context": True,
            "context": "This is additional context",
        }

        result = self.manager.render_chat_prompt(context)
        assert "Example 1" in result
        assert "Example response 1" in result

    def test_template_with_conditional_sections(self):
        """Test templates with conditional sections."""
        context_with_examples = {
            "prompt": "Test prompt",
            "include_examples": True,
            "examples": ["Example 1", "Example 2"],
        }

        context_without_examples = {
            "prompt": "Test prompt",
            "include_examples": False,
        }

        with_examples = self.manager.render_text_prompt(context_with_examples)
        without_examples = self.manager.render_text_prompt(context_without_examples)

        assert "Examples:" in with_examples
        assert "Examples:" not in without_examples

    def test_template_performance(self):
        """Test template rendering performance."""
        context = {
            "messages": [{"role": "user", "content": "Performance test message"}]
        }

        import time

        start_time = time.time()
        for _ in range(100):
            self.manager.render_chat_prompt(context)
        duration = time.time() - start_time

        # Should complete 100 renders in under 1 second
        assert duration < 1.0

    def test_template_caching(self):
        """Test template caching functionality."""
        original_stats = self.manager.get_template_stats()
        original_cache_size = original_stats["cache_size"]

        # Render multiple times to trigger caching
        context = {"messages": [{"role": "user", "content": "test"}]}
        for _ in range(10):
            self.manager.render_chat_prompt(context)

        new_stats = self.manager.get_template_stats()
        # Cache should have entries
        assert new_stats["cache_size"] >= original_cache_size

    def test_template_reload(self):
        """Test template reloading."""
        original_templates = self.manager.get_template_stats()["available_templates"]

        self.manager.reload_templates()
        new_templates = self.manager.get_template_stats()["available_templates"]

        assert original_templates == new_templates

    def test_template_error_handling(self):
        """Test template error handling."""
        # Test with invalid template name
        with pytest.raises(ValueError):
            self.manager.validate_template_variables("nonexistent.j2", {})

        # Test rendering with invalid context
        valid_context = {"messages": [{"role": "user", "content": "test"}]}

        # Should not raise error with valid context
        result = self.manager.render_chat_prompt(valid_context)
        assert isinstance(result, str)

    def test_security_context_sanitization(self):
        """Test template security with user input."""
        # Test with potentially malicious content
        malicious_context = {
            "messages": [{"role": "user", "content": "<script>alert('xss')</script>"}]
        }

        result = self.manager.render_chat_prompt(malicious_context)
        # Content should be preserved but not executed
        assert "<script>alert('xss')</script>" in result
        assert isinstance(result, str)


class TestTemplateBenchmarks:
    """Performance benchmarks for templates."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TemplateManager()

    def test_large_context_performance(self):
        """Test performance with large contexts."""
        large_context = {
            "messages": [
                {"role": "user", "content": "x" * 1000},
                {"role": "assistant", "content": "y" * 1000},
            ]
            * 10,
            "system_message": "z" * 500,
        }

        start_time = time.time()
        result = self.manager.render_chat_prompt(large_context)
        duration = time.time() - start_time

        assert isinstance(result, str)
        assert len(result) > 20000  # Large context
        assert duration < 2.0  # Should complete within 2 seconds

    def test_repeated_rendering_performance(self):
        """Test caching performance with repeated renders."""
        context = {
            "prompt": "Benchmark test",
            "constraints": ["constraint1", "constraint2", "constraint3"],
            "format": "JSON",
            "tone": "professional",
        }

        # First render (cold cache)
        start_time = time.time()
        self.manager.render_text_prompt(context)
        first_duration = time.time() - start_time

        # Subsequent renders (warm cache)
        start_time = time.time()
        for _ in range(100):
            self.manager.render_text_prompt(context)
        warm_duration = time.time() - start_time

        # Warm renders should be faster
        assert warm_duration < first_duration * 10  # Should be much faster
