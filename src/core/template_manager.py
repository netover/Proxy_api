"""
Jinja2 Template Manager for dynamic prompt assembly and response formatting.
Provides template validation, caching, and performance optimization.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import (Environment, FileSystemLoader, TemplateNotFound,
                    TemplateSyntaxError)
from jinja2.exceptions import UndefinedError

from .logging import ContextualLogger
from .telemetry import TracedSpan, traced

logger = ContextualLogger(__name__)


class TemplateManager:
    """Manages Jinja2 templates for prompt assembly and response formatting."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize the template manager with caching and validation."""
        self.template_dir = template_dir or str(Path(__file__).parent.parent.parent / "templates")
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False,  # Safe for text generation
            trim_blocks=True,
            lstrip_blocks=True,
            cache_size=1000
        )
        self._validate_templates()
        logger.info(f"Template manager initialized with directory: {self.template_dir}")
        
    def _validate_templates(self) -> None:
        """Validate all templates on initialization."""
        template_names = ["prompt_chat.j2", "prompt_text.j2"]
        for template_name in template_names:
            try:
                template = self.env.get_template(template_name)
                # Basic syntax validation
                template.render({})
                logger.info(f"Template validated: {template_name}")
            except TemplateNotFound:
                logger.warning(f"Template not found: {template_name}")
            except TemplateSyntaxError as e:
                logger.error(f"Template syntax error in {template_name}: {e}")
            except Exception as e:
                logger.error(f"Error validating template {template_name}: {e}")
                
    @traced("template.render", attributes={"operation": "template_rendering"})
    def render_chat_prompt(self, context: Dict[str, Any]) -> str:
        """Render chat completion prompt using chat template."""
        try:
            template = self.env.get_template("prompt_chat.j2")
            with TracedSpan("template.render_chat", attributes={
                "template.name": "prompt_chat.j2",
                "context.keys": list(context.keys())
            }) as span:
                result = template.render(context)
                span.set_attribute("result.length", len(result))
                return result
        except TemplateNotFound:
            logger.error("Chat template not found")
            raise ValueError("Chat template 'prompt_chat.j2' not found")
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise ValueError(f"Template syntax error: {e}")
        except UndefinedError as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Template rendering error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error rendering chat prompt: {e}")
            raise ValueError(f"Failed to render chat prompt: {e}")
            
    @traced("template.render", attributes={"operation": "template_rendering"})
    def render_text_prompt(self, context: Dict[str, Any]) -> str:
        """Render text completion prompt using text template."""
        try:
            template = self.env.get_template("prompt_text.j2")
            with TracedSpan("template.render_text", attributes={
                "template.name": "prompt_text.j2",
                "context.keys": list(context.keys())
            }) as span:
                result = template.render(context)
                span.set_attribute("result.length", len(result))
                return result
        except TemplateNotFound:
            logger.error("Text template not found")
            raise ValueError("Text template 'prompt_text.j2' not found")
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise ValueError(f"Template syntax error: {e}")
        except UndefinedError as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Template rendering error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error rendering text prompt: {e}")
            raise ValueError(f"Failed to render text prompt: {e}")
            
    def validate_template_variables(self, template_name: str, variables: Dict[str, Any]) -> bool:
        """Validate if all required template variables are provided."""
        try:
            template = self.env.get_template(template_name)
            # Extract variable dependencies from template
            from jinja2.meta import find_undeclared_variables
            ast = self.env.parse(template.source)
            required_vars = find_undeclared_variables(ast)
            
            provided_vars = set(variables.keys())
            missing_vars = required_vars - provided_vars
            
            if missing_vars:
                logger.warning(f"Missing template variables for {template_name}: {missing_vars}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error validating template variables: {e}")
            return False
            
    def get_template_stats(self) -> Dict[str, Any]:
        """Get template statistics and cache information."""
        return {
            "template_directory": self.template_dir,
            "available_templates": self.env.list_templates(),
            "cache_size": len(self.env.cache),
            "template_count": len(self.env.loader.list_templates())
        }
            
    def reload_templates(self) -> None:
        """Reload templates from disk."""
        self.env.cache.clear()
        self._validate_templates()
        logger.info("Templates reloaded")


# Global template manager instance
template_manager = TemplateManager()