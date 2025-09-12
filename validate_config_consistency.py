#!/usr/bin/env python3
"""
Validation script for model config mapping and provider instances.
Validates configuration consistency and tests provider lifecycle management.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.unified_config import config_manager, ProviderType
from src.core.provider_factory import provider_factory
from src.core.logging import ContextualLogger

logger = ContextualLogger(__name__)

class ConfigValidator:
    """Validates configuration consistency and provider mappings"""

    def __init__(self):
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def log_issue(self, message: str):
        """Log a validation issue"""
        self.issues.append(message)
        logger.error(f"VALIDATION ISSUE: {message}")

    def log_warning(self, message: str):
        """Log a validation warning"""
        self.warnings.append(message)
        logger.warning(f"VALIDATION WARNING: {message}")

    def validate_provider_mappings(self) -> bool:
        """Validate that PROVIDER_MAPPING matches actual provider classes"""
        logger.info("Validating provider mappings...")

        from src.core.provider_factory import ProviderFactory

        mapping = ProviderFactory.PROVIDER_MAPPING
        success = True

        for provider_type, (module_path, class_name) in mapping.items():
            try:
                # Try to import the module
                module = __import__(module_path, fromlist=[class_name])

                # Check if class exists
                if not hasattr(module, class_name):
                    self.log_issue(f"Provider class '{class_name}' not found in {module_path}")
                    success = False
                    continue

                provider_class = getattr(module, class_name)

                # Check if it inherits from BaseProvider
                from src.core.provider_factory import BaseProvider
                if not issubclass(provider_class, BaseProvider):
                    self.log_issue(f"Provider class '{class_name}' does not inherit from BaseProvider")
                    success = False

                logger.info(f"✓ Provider mapping validated: {provider_type.value} -> {module_path}.{class_name}")

            except ImportError as e:
                self.log_issue(f"Failed to import provider module {module_path}: {e}")
                success = False
            except Exception as e:
                self.log_issue(f"Error validating provider {provider_type.value}: {e}")
                success = False

        return success

    def validate_config_consistency(self) -> bool:
        """Validate consistency between different config sources"""
        logger.info("Validating configuration consistency...")

        success = True

        try:
            # Load unified config
            config = config_manager.load_config()

            # Check model selections file
            model_selections_path = Path("config/model_selections.json")
            if model_selections_path.exists():
                with open(model_selections_path, 'r') as f:
                    model_selections = json.load(f)

                # Validate that selected models exist in provider configs
                for provider_name, selection in model_selections.items():
                    provider_config = config_manager.get_provider_by_name(provider_name)
                    if not provider_config:
                        self.log_issue(f"Model selection for unknown provider: {provider_name}")
                        success = False
                        continue

                    selected_model = selection.get('model_name')
                    if selected_model and selected_model not in provider_config.models:
                        self.log_issue(f"Selected model '{selected_model}' not supported by provider '{provider_name}'")
                        success = False

                logger.info("✓ Model selections validated against provider configs")
            else:
                self.log_warning("Model selections file not found")

        except Exception as e:
            self.log_issue(f"Error validating config consistency: {e}")
            success = False

        return success

    async def validate_provider_instances(self) -> bool:
        """Test provider instance creation and lifecycle"""
        logger.info("Testing provider instance creation and lifecycle...")

        success = True

        try:
            # Load config
            config = config_manager.load_config()

            # Test creating provider instances
            for provider_config in config.providers:
                if not provider_config.enabled:
                    logger.info(f"Skipping disabled provider: {provider_config.name}")
                    continue

                try:
                    # Create provider instance
                    provider = await provider_factory.create_provider(provider_config)
                    logger.info(f"✓ Created provider instance: {provider_config.name}")

                    # Test health check
                    health_result = await provider.health_check()
                    if health_result.get('healthy'):
                        logger.info(f"✓ Health check passed for: {provider_config.name}")
                    else:
                        self.log_warning(f"Health check failed for {provider_config.name}: {health_result.get('error', 'Unknown error')}")

                    # Test cleanup
                    await provider.close()
                    logger.info(f"✓ Provider cleanup successful: {provider_config.name}")

                except Exception as e:
                    self.log_issue(f"Error with provider {provider_config.name}: {e}")
                    success = False

        except Exception as e:
            self.log_issue(f"Error testing provider instances: {e}")
            success = False

        return success

    def validate_model_mappings(self) -> bool:
        """Validate model-to-provider mappings"""
        logger.info("Validating model-to-provider mappings...")

        success = True

        try:
            config = config_manager.load_config()

            # Collect all models and their providers
            model_providers: Dict[str, List[str]] = {}

            for provider_config in config.providers:
                if not provider_config.enabled:
                    continue

                for model in provider_config.models:
                    if model not in model_providers:
                        model_providers[model] = []
                    model_providers[model].append(provider_config.name)

            # Check for models supported by multiple providers
            for model, providers in model_providers.items():
                if len(providers) > 1:
                    logger.info(f"Model '{model}' supported by multiple providers: {providers}")

            # Check for orphaned model selections
            model_selections_path = Path("config/model_selections.json")
            if model_selections_path.exists():
                with open(model_selections_path, 'r') as f:
                    model_selections = json.load(f)

                for provider_name in model_selections.keys():
                    if not config_manager.get_provider_by_name(provider_name):
                        self.log_issue(f"Model selection exists for non-existent provider: {provider_name}")
                        success = False

            logger.info(f"✓ Validated mappings for {len(model_providers)} models")

        except Exception as e:
            self.log_issue(f"Error validating model mappings: {e}")
            success = False

        return success

    async def run_validation(self) -> bool:
        """Run all validation checks"""
        logger.info("Starting configuration validation...")

        results = []

        # Run all validation checks
        results.append(("Provider Mappings", self.validate_provider_mappings()))
        results.append(("Config Consistency", self.validate_config_consistency()))
        results.append(("Model Mappings", self.validate_model_mappings()))
        results.append(("Provider Instances", await self.validate_provider_instances()))

        # Summary
        total_checks = len(results)
        passed_checks = sum(1 for _, passed in results if passed)

        logger.info(f"Validation complete: {passed_checks}/{total_checks} checks passed")

        if self.issues:
            logger.error(f"Found {len(self.issues)} issues:")
            for issue in self.issues:
                logger.error(f"  - {issue}")

        if self.warnings:
            logger.warning(f"Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")

        return len(self.issues) == 0

async def main():
    """Main validation function"""
    validator = ConfigValidator()
    success = await validator.run_validation()

    if success:
        logger.info("✅ All validations passed!")
        return 0
    else:
        logger.error("❌ Validation failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)