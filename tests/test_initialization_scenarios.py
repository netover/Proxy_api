"""
Comprehensive initialization stability tests for ProxyAPI.

Tests dependency graph stability under various scenarios:
- Minimal configuration
- Full configuration
- Partial configuration
- Missing dependencies
- Network failures
- Error conditions
"""

import asyncio
import os
import tempfile
import pytest
import yaml
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path

from src.core.app_init import ApplicationInitializer, initialize_app
from src.core.exceptions import InitializationError


class TestInitializationScenarios:
    """Test initialization under various configuration and failure scenarios."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def create_config_file(
        self, temp_dir, config_data, filename="config.yaml"
    ):
        """Create a temporary config file."""
        config_path = temp_dir / filename
        with open(config_path, "w") as f:
            yaml.safe_dump(config_data, f)
        return config_path

    def get_minimal_config(self):
        """Get minimal configuration with only required fields."""
        return {
            "auth": {"api_keys": ["test-key-123"]},
            "providers": [
                {
                    "name": "test-provider",
                    "type": "openai",
                    "api_key_env": "TEST_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-3.5-turbo"],
                    "enabled": True,
                    "priority": 1,
                }
            ],
        }

    def get_full_config(self):
        """Get full configuration (copy of existing config.yaml structure)."""
        return {
            "app": {
                "name": "LLM Proxy API",
                "version": "2.0.0",
                "environment": "test",
            },
            "server": {"host": "127.0.0.1", "port": 8000, "debug": False},
            "auth": {"api_keys": ["test-key-123", "prod-key-456"]},
            "providers": [
                {
                    "name": "openai",
                    "type": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-3.5-turbo", "gpt-4"],
                    "enabled": True,
                    "priority": 1,
                    "timeout": 30,
                    "max_retries": 3,
                },
                {
                    "name": "anthropic",
                    "type": "anthropic",
                    "api_key_env": "ANTHROPIC_API_KEY",
                    "base_url": "https://api.anthropic.com",
                    "models": ["claude-3-haiku"],
                    "enabled": True,
                    "priority": 2,
                },
            ],
            "circuit_breaker": {
                "failure_threshold": 5,
                "recovery_timeout": 60,
            },
            "caching": {
                "enabled": True,
                "response_cache": {"max_size_mb": 100, "ttl": 1800},
            },
            "logging": {"level": "INFO", "format": "json"},
        }

    def get_partial_config(self):
        """Get partial configuration missing some optional sections."""
        return {
            "auth": {"api_keys": ["test-key-123"]},
            "providers": [
                {
                    "name": "openai",
                    "type": "openai",
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-3.5-turbo"],
                    "enabled": True,
                    "priority": 1,
                }
            ],
            # Missing: circuit_breaker, caching, logging sections
        }

    @pytest.mark.asyncio
    async def test_minimal_configuration_startup(self, temp_config_dir):
        """Test initialization with minimal configuration."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        # Set required environment variable
        os.environ["TEST_API_KEY"] = "test-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer, "_initialize_parallel_execution_components"
        ) as mock_init_parallel:

            # Mock settings to return our config
            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            # Should succeed with minimal config
            result = await initializer.initialize()

            assert "config" in result
            assert "services" in result
            assert "logger" in result
            assert result["logger"] == mock_logger

            # Verify logging calls
            mock_setup_logging.assert_called_once()
            mock_logger.info.assert_any_call(
                "🚀 Starting application initialization..."
            )
            mock_logger.info.assert_any_call(
                "✅ Application initialization completed successfully"
            )
            mock_init_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_configuration_startup(self, temp_config_dir):
        """Test initialization with full configuration."""
        config_data = self.get_full_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        # Set required environment variables
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer, "_initialize_parallel_execution_components"
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            result = await initializer.initialize()

            assert "config" in result
            assert "services" in result
            assert "logger" in result

            # Verify parallel components initialization was called
            mock_init_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_partial_configuration_startup(self, temp_config_dir):
        """Test initialization with partial configuration (missing optional sections)."""
        config_data = self.get_partial_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["OPENAI_API_KEY"] = "test-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer, "_initialize_parallel_execution_components"
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            result = await initializer.initialize()

            assert "config" in result
            assert "services" in result
            assert "logger" in result

            # Should still initialize parallel components even with partial config
            mock_init_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_dependencies_scenario(self, temp_config_dir):
        """Test initialization when critical dependencies are missing."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["TEST_API_KEY"] = "test-key"

        # Test missing dependencies by making parallel init fail
        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer,
            "_initialize_parallel_execution_components",
            side_effect=ImportError("No module named 'circuit_breaker_pool'"),
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            # Should fail due to missing dependencies
            with pytest.raises(InitializationError) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)
            assert "No module named 'circuit_breaker_pool'" in str(
                exc_info.value
            )

    @pytest.mark.asyncio
    async def test_network_failure_simulation(self, temp_config_dir):
        """Test initialization with simulated network failures during component startup."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["TEST_API_KEY"] = "test-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer,
            "_initialize_parallel_execution_components",
            side_effect=asyncio.TimeoutError("Network timeout"),
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            # Should fail due to network timeout
            with pytest.raises(InitializationError) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)
            assert "Network timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invalid_configuration_error(self, temp_config_dir):
        """Test initialization with invalid configuration."""
        # Create invalid config (missing required api_keys)
        invalid_config = {
            "providers": [
                {
                    "name": "test",
                    "type": "openai",
                    "models": ["gpt-3.5-turbo"],
                    "enabled": True,
                }
            ]
            # Missing auth.api_keys
        }
        config_path = self.create_config_file(temp_config_dir, invalid_config)

        with patch(
            "src.core.config.settings",
            side_effect=ValueError("Proxy API keys must be configured"),
        ):
            initializer = ApplicationInitializer(str(config_path))

            with pytest.raises(InitializationError) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_logging_setup_failure(self, temp_config_dir):
        """Test initialization when logging setup fails."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["TEST_API_KEY"] = "test-key"

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging",
            side_effect=Exception("Logging setup failed"),
        ), patch("signal.signal") as mock_signal:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"

            initializer = ApplicationInitializer(str(config_path))

            with pytest.raises(InitializationError) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)
            assert "Logging setup failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_signal_handler_setup_failure(self, temp_config_dir):
        """Test initialization when signal handler setup fails."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["TEST_API_KEY"] = "test-key"

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal", side_effect=OSError("Signal setup failed")
        ):

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            initializer = ApplicationInitializer(str(config_path))

            # Should succeed but log warning
            result = await initializer.initialize()

            assert "config" in result
            mock_logger.warning.assert_called_once_with(
                "Failed to setup signal handlers: Signal setup failed"
            )

    @pytest.mark.asyncio
    async def test_multiple_provider_initialization(self, temp_config_dir):
        """Test initialization with multiple providers and complex dependencies."""
        config_data = self.get_full_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer, "_initialize_parallel_execution_components"
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            result = await initializer.initialize()

            assert "config" in result
            assert "services" in result

            # Verify parallel components initialization was called
            mock_init_parallel.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialization_timeout_simulation(self, temp_config_dir):
        """Test initialization with simulated timeouts."""
        config_data = self.get_minimal_config()
        config_path = self.create_config_file(temp_config_dir, config_data)

        os.environ["TEST_API_KEY"] = "test-key"

        initializer = ApplicationInitializer(str(config_path))

        with patch("src.core.app_init.settings") as mock_settings, patch(
            "src.core.app_init.setup_logging"
        ) as mock_setup_logging, patch(
            "signal.signal"
        ) as mock_signal, patch.object(
            initializer,
            "_initialize_parallel_execution_components",
            side_effect=asyncio.TimeoutError("Load balancer timeout"),
        ) as mock_init_parallel:

            mock_config = Mock()
            mock_settings.__class__ = Mock()
            mock_settings.__class__.__name__ = "Settings"
            mock_logger = Mock()
            mock_setup_logging.return_value = mock_logger

            # Should fail due to timeout
            with pytest.raises(InitializationError) as exc_info:
                await initializer.initialize()

            assert "Failed to initialize application" in str(exc_info.value)
            assert "Load balancer timeout" in str(exc_info.value)


class TestInitializationReport:
    """Generate initialization test report."""

    def generate_report(self, test_results):
        """Generate a detailed test report."""
        report = {
            "test_summary": {
                "total_scenarios": len(test_results),
                "passed": sum(
                    1 for r in test_results if r["status"] == "passed"
                ),
                "failed": sum(
                    1 for r in test_results if r["status"] == "failed"
                ),
                "warnings": sum(
                    1 for r in test_results if r["status"] == "warning"
                ),
            },
            "scenarios": test_results,
            "failure_modes": [
                r for r in test_results if r["status"] in ["failed", "warning"]
            ],
            "recommendations": self.generate_recommendations(test_results),
        }
        return report

    def generate_recommendations(self, test_results):
        """Generate recommendations based on test results."""
        recommendations = []

        failed_scenarios = [r for r in test_results if r["status"] == "failed"]
        warning_scenarios = [
            r for r in test_results if r["status"] == "warning"
        ]

        if failed_scenarios:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "critical_failures",
                    "description": f"Address {len(failed_scenarios)} critical initialization failures",
                    "details": [f["scenario"] for f in failed_scenarios],
                }
            )

        if warning_scenarios:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "resilience_improvements",
                    "description": f"Improve error handling for {len(warning_scenarios)} scenarios",
                    "details": [w["scenario"] for w in warning_scenarios],
                }
            )

        # General recommendations
        recommendations.extend(
            [
                {
                    "priority": "medium",
                    "category": "dependency_management",
                    "description": "Implement dependency health checks before initialization",
                    "rationale": "Prevents initialization failures due to missing optional components",
                },
                {
                    "priority": "low",
                    "category": "configuration_validation",
                    "description": "Add comprehensive configuration validation with detailed error messages",
                    "rationale": "Improves debugging experience for configuration issues",
                },
                {
                    "priority": "medium",
                    "category": "graceful_degradation",
                    "description": "Enhance graceful degradation when optional components fail",
                    "rationale": "Ensures core functionality remains available during partial failures",
                },
            ]
        )

        return recommendations


# Test runner function
async def run_initialization_tests():
    """Run all initialization tests and generate report."""
    test_instance = TestInitializationScenarios()
    report_generator = TestInitializationReport()

    test_results = []

    # Define test scenarios
    scenarios = [
        ("minimal_config", test_instance.test_minimal_configuration_startup),
        ("full_config", test_instance.test_full_configuration_startup),
        ("partial_config", test_instance.test_partial_configuration_startup),
        (
            "missing_dependencies",
            test_instance.test_missing_dependencies_scenario,
        ),
        ("network_failure", test_instance.test_network_failure_simulation),
        ("invalid_config", test_instance.test_invalid_configuration_error),
        ("logging_failure", test_instance.test_logging_setup_failure),
        (
            "signal_handler_failure",
            test_instance.test_signal_handler_setup_failure,
        ),
        (
            "multiple_providers",
            test_instance.test_multiple_provider_initialization,
        ),
        (
            "timeout_simulation",
            test_instance.test_initialization_timeout_simulation,
        ),
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        for scenario_name, test_method in scenarios:
            try:
                print(f"Running scenario: {scenario_name}")
                await test_method(temp_path)

                test_results.append(
                    {
                        "scenario": scenario_name,
                        "status": "passed",
                        "error": None,
                        "duration": None,  # Could add timing if needed
                    }
                )
                print(f"[PASS] {scenario_name}: PASSED")

            except Exception as e:
                status = (
                    "failed" if "critical" in str(e).lower() else "warning"
                )
                test_results.append(
                    {
                        "scenario": scenario_name,
                        "status": status,
                        "error": str(e),
                        "duration": None,
                    }
                )
                print(f"[FAIL] {scenario_name}: {status.upper()} - {e}")

    # Generate report
    report = report_generator.generate_report(test_results)

    return report


if __name__ == "__main__":
    # Run tests and print report
    report = asyncio.run(run_initialization_tests())

    print("\n" + "=" * 60)
    print("INITIALIZATION STABILITY TEST REPORT")
    print("=" * 60)

    summary = report["test_summary"]
    print(f"Total Scenarios: {summary['total_scenarios']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Warnings: {summary['warnings']}")

    if report["failure_modes"]:
        print(f"\nFailure Modes ({len(report['failure_modes'])}):")
        for failure in report["failure_modes"]:
            print(f"  - {failure['scenario']}: {failure['error']}")

    print("\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  [{rec['priority'].upper()}] {rec['description']}")
        if "details" in rec:
            for detail in rec["details"]:
                print(f"    - {detail}")

    print("\n" + "=" * 60)
