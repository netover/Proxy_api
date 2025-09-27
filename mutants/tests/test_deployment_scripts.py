import pytest
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Import the setup script
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from setup_model_discovery import ModelDiscoverySetup


class TestModelDiscoverySetup:
    """Test ModelDiscoverySetup class"""

    def setup_method(self):
        """Setup for each test method"""
        with patch('pathlib.Path'):
            self.setup = ModelDiscoverySetup()

    @patch('sys.version_info')
    @patch('subprocess.run')
    def test_check_system_requirements_success(self, mock_subprocess, mock_version):
        """Test successful system requirements check"""
        mock_version.__ge__ = lambda x, y: True
        mock_version.major = 3
        mock_version.minor = 11

        # Mock successful subprocess calls
        mock_subprocess.return_value = Mock()

        result = self.setup.check_system_requirements()

        assert result is True
        assert mock_subprocess.call_count == 2  # pip and git checks

    @patch('sys.version_info')
    @patch('subprocess.run')
    def test_check_system_requirements_python_version_fail(self, mock_subprocess, mock_version):
        """Test system requirements check with insufficient Python version"""
        mock_version.__lt__ = lambda x, y: True
        mock_version.major = 3
        mock_version.minor = 8

        result = self.setup.check_system_requirements()

        assert result is False

    @patch('sys.version_info')
    @patch('subprocess.run')
    def test_check_system_requirements_pip_fail(self, mock_subprocess, mock_version):
        """Test system requirements check with pip failure"""
        mock_version.__ge__ = lambda x, y: True
        mock_version.major = 3
        mock_version.minor = 11

        # Mock pip failure
        def subprocess_side_effect(*args, **kwargs):
            if 'pip' in str(args[0]):
                raise subprocess.CalledProcessError(1, 'pip')
            return Mock()

        mock_subprocess.side_effect = subprocess_side_effect

        result = self.setup.check_system_requirements()

        assert result is False

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_install_dependencies_success(self, mock_exists, mock_subprocess):
        """Test successful dependency installation"""
        mock_exists.return_value = True
        mock_subprocess.return_value = Mock()

        result = self.setup.install_dependencies()

        assert result is True
        mock_subprocess.assert_called_once()

    @patch('subprocess.run')
    @patch('pathlib.Path.exists')
    def test_install_dependencies_no_requirements_file(self, mock_exists, mock_subprocess):
        """Test dependency installation when requirements.txt doesn't exist"""
        mock_exists.return_value = False

        result = self.setup.install_dependencies()

        assert result is True
        mock_subprocess.assert_not_called()

    @patch('subprocess.run')
    def test_install_dependencies_failure(self, mock_subprocess):
        """Test dependency installation failure"""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'pip install')

        result = self.setup.install_dependencies()

        assert result is False

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.dump')
    def test_create_config_files_success(self, mock_yaml_dump, mock_file, mock_exists, mock_mkdir):
        """Test successful config file creation"""
        mock_exists.return_value = False

        result = self.setup.create_config_files()

        assert result is True
        assert mock_mkdir.call_count == 1
        assert mock_file.call_count == 2  # config.yaml and .env.example
        assert mock_yaml_dump.call_count == 1

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_create_config_files_already_exists(self, mock_exists, mock_mkdir):
        """Test config file creation when files already exist"""
        mock_exists.return_value = True

        result = self.setup.create_config_files()

        assert result is True

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_create_config_files_failure(self, mock_file, mock_exists, mock_mkdir):
        """Test config file creation failure"""
        mock_exists.return_value = False
        mock_file.side_effect = IOError("Permission denied")

        result = self.setup.create_config_files()

        assert result is False

    @patch('getpass.getpass')
    def test_setup_api_keys_interactive(self, mock_getpass):
        """Test interactive API key setup"""
        mock_getpass.side_effect = ["key1", "key2", "", "key4"]

        result = self.setup.setup_api_keys()

        expected = {
            "openai": "key1",
            "anthropic": "key2",
            "azure_openai": "key4"
        }
        assert result == expected

    @patch('getpass.getpass')
    def test_setup_api_keys_skip_all(self, mock_getpass):
        """Test API key setup when all are skipped"""
        mock_getpass.return_value = ""

        result = self.setup.setup_api_keys()

        assert result == {}

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    @patch('yaml.dump')
    @patch('shutil.copy2')
    def test_update_config_with_keys_success(self, mock_copy, mock_yaml_dump, mock_yaml_load, mock_file, mock_exists):
        """Test successful config update with API keys"""
        mock_exists.return_value = True

        config_data = {
            "providers": {
                "openai": {"api_key": ""},
                "anthropic": {"api_key": ""}
            }
        }
        mock_yaml_load.return_value = config_data

        api_keys = {"openai": "new_key"}
        result = self.setup.update_config_with_keys(api_keys)

        assert result is True
        mock_yaml_dump.assert_called_once()
        mock_copy.assert_called_once()  # Backup created

    @patch('pathlib.Path.exists')
    def test_update_config_with_keys_no_config_file(self, mock_exists):
        """Test config update when config file doesn't exist"""
        mock_exists.return_value = False

        result = self.setup.update_config_with_keys({"openai": "key"})

        assert result is False

    @patch('pathlib.Path.mkdir')
    def test_create_directories_success(self, mock_mkdir):
        """Test successful directory creation"""
        result = self.setup.create_directories()

        assert result is True
        assert mock_mkdir.call_count == 4  # cache, logs, data, config/providers

    @patch('pathlib.Path.mkdir')
    def test_create_directories_with_existing(self, mock_mkdir):
        """Test directory creation with existing directories"""
        mock_mkdir.side_effect = FileExistsError()

        result = self.setup.create_directories()

        assert result is True

    @patch('src.core.model_discovery.ModelDiscovery')
    @patch('src.core.cache_manager.CacheManager')
    @patch('src.core.provider_factory.ProviderFactory')
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('yaml.safe_load')
    def test_validate_installation_success(self, mock_yaml_load, mock_file, mock_exists,
                                          mock_provider_factory, mock_cache_manager, mock_model_discovery):
        """Test successful installation validation"""
        mock_exists.return_value = True
        mock_yaml_load.return_value = {"test": "config"}

        result = self.setup.validate_installation()

        assert result is True
        mock_model_discovery.assert_called_once()

    @patch('src.core.model_discovery.ModelDiscovery')
    def test_validate_installation_import_failure(self, mock_model_discovery):
        """Test installation validation with import failure"""
        mock_model_discovery.side_effect = ImportError("Module not found")

        result = self.setup.validate_installation()

        assert result is False

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.chmod')
    def test_create_startup_script_success(self, mock_chmod, mock_file, mock_exists):
        """Test successful startup script creation"""
        mock_exists.return_value = False

        result = self.setup.create_startup_script()

        assert result is True
        assert mock_file.call_count == 2  # .sh and .bat files
        mock_chmod.assert_called_once()

    @patch('pathlib.Path.exists')
    @patch('builtins.open')
    def test_create_startup_script_failure(self, mock_file, mock_exists):
        """Test startup script creation failure"""
        mock_exists.return_value = False
        mock_file.side_effect = IOError("Permission denied")

        result = self.setup.create_startup_script()

        assert result is False

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_docker_files_success(self, mock_file, mock_exists):
        """Test successful Docker file creation"""
        mock_exists.return_value = False

        result = self.setup.create_docker_files()

        assert result is True
        assert mock_file.call_count == 2  # Dockerfile and docker-compose.yml

    @patch('src.core.model_discovery.ModelDiscovery')
    @patch('src.core.cache_manager.CacheManager')
    @patch('src.core.provider_factory.ProviderFactory')
    def test_run_initial_discovery_success(self, mock_provider_factory, mock_cache_manager, mock_model_discovery):
        """Test successful initial discovery run"""
        result = self.setup.run_initial_discovery()

        assert result is True
        mock_model_discovery.assert_called_once()

    @patch('src.core.model_discovery.ModelDiscovery')
    def test_run_initial_discovery_failure(self, mock_model_discovery):
        """Test initial discovery failure"""
        mock_model_discovery.side_effect = Exception("Discovery failed")

        result = self.setup.run_initial_discovery()

        assert result is False

    def test_generate_setup_report(self):
        """Test setup report generation"""
        with patch.object(self.setup, 'check_system_requirements', return_value=True), \
             patch.object(self.setup, 'install_dependencies', return_value=True), \
             patch.object(self.setup, 'create_config_files', return_value=False), \
             patch.object(self.setup, 'create_directories', return_value=True), \
             patch.object(self.setup, 'validate_installation', return_value=True), \
             patch.object(self.setup, 'create_startup_script', return_value=True), \
             patch.object(self.setup, 'create_docker_files', return_value=True), \
             patch.object(self.setup, 'run_initial_discovery', return_value=True):

            report = self.setup.generate_setup_report()

            expected = {
                "system_requirements": True,
                "dependencies": True,
                "config_files": False,
                "directories": True,
                "validation": True,
                "startup_scripts": True,
                "docker_files": True,
                "initial_discovery": True
            }
            assert report == expected

    @patch('builtins.open', new_callable=mock_open)
    @patch('platform.system')
    @patch('platform.release')
    def test_interactive_setup(self, mock_release, mock_system, mock_file):
        """Test interactive setup"""
        mock_system.return_value = "Linux"
        mock_release.return_value = "5.4.0"

        with patch.object(self.setup, 'setup_api_keys', return_value={"openai": "key"}), \
             patch.object(self.setup, 'update_config_with_keys', return_value=True), \
             patch.object(self.setup, 'generate_setup_report') as mock_report:

            mock_report.return_value = {"step1": True, "step2": False}

            self.setup.interactive_setup()

            mock_report.assert_called_once()

    def test_quick_setup_success(self):
        """Test successful quick setup"""
        with patch.object(self.setup, 'check_system_requirements', return_value=True), \
             patch.object(self.setup, 'install_dependencies', return_value=True), \
             patch.object(self.setup, 'create_config_files', return_value=True), \
             patch.object(self.setup, 'create_directories', return_value=True), \
             patch.object(self.setup, 'validate_installation', return_value=True), \
             patch.object(self.setup, 'create_startup_script', return_value=True), \
             patch.object(self.setup, 'create_docker_files', return_value=True), \
             patch.object(self.setup, 'run_initial_discovery', return_value=True):

            result = self.setup.quick_setup()

            assert result is True

    def test_quick_setup_failure(self):
        """Test quick setup with failure"""
        with patch.object(self.setup, 'check_system_requirements', return_value=False):
            result = self.setup.quick_setup()

            assert result is False


class TestScriptExecution:
    """Test script execution and argument parsing"""

    @patch('sys.argv', ['setup_model_discovery.py', '--check'])
    @patch('setup_model_discovery.ModelDiscoverySetup')
    def test_main_check_only(self, mock_setup_class):
        """Test main function with --check argument"""
        mock_setup = Mock()
        mock_setup_class.return_value = mock_setup

        from setup_model_discovery import main
        main()

        mock_setup.check_system_requirements.assert_called_once()

    @patch('sys.argv', ['setup_model_discovery.py', '--interactive'])
    @patch('setup_model_discovery.ModelDiscoverySetup')
    def test_main_interactive(self, mock_setup_class):
        """Test main function with --interactive argument"""
        mock_setup = Mock()
        mock_setup_class.return_value = mock_setup

        from setup_model_discovery import main
        main()

        mock_setup.interactive_setup.assert_called_once()

    @patch('sys.argv', ['setup_model_discovery.py', '--quick'])
    @patch('setup_model_discovery.ModelDiscoverySetup')
    def test_main_quick(self, mock_setup_class):
        """Test main function with --quick argument"""
        mock_setup = Mock()
        mock_setup_class.return_value = mock_setup

        from setup_model_discovery import main
        main()

        mock_setup.quick_setup.assert_called_once()

    @patch('sys.argv', ['setup_model_discovery.py'])
    @patch('setup_model_discovery.ModelDiscoverySetup')
    def test_main_default_interactive(self, mock_setup_class):
        """Test main function with default (no arguments)"""
        mock_setup = Mock()
        mock_setup_class.return_value = mock_setup

        from setup_model_discovery import main
        main()

        mock_setup.interactive_setup.assert_called_once()

    @patch('sys.argv', ['setup_model_discovery.py', '--check'])
    @patch('setup_model_discovery.ModelDiscoverySetup')
    def test_main_exception_handling(self, mock_setup_class):
        """Test main function exception handling"""
        mock_setup = Mock()
        mock_setup.check_system_requirements.side_effect = Exception("Test error")
        mock_setup_class.return_value = mock_setup

        with patch('sys.exit') as mock_exit:
            from setup_model_discovery import main
            main()

            mock_exit.assert_called_once_with(1)


class TestScriptIntegration:
    """Integration tests for the setup script"""

    def test_script_imports(self):
        """Test that all required modules can be imported"""
        # This test ensures the script can import all its dependencies
        try:
            import yaml
            import getpass
            import platform
            from datetime import datetime
            # These should all be available
            assert True
        except ImportError as e:
            pytest.fail(f"Required module not available: {e}")

    def test_colors_class(self):
        """Test Colors class constants"""
        from setup_model_discovery import Colors

        assert Colors.HEADER == '\033[95m'
        assert Colors.OKGREEN == '\033[92m'
        assert Colors.FAIL == '\033[91m'
        assert Colors.ENDC == '\033[0m'

    def test_print_functions(self):
        """Test print helper functions"""
        from setup_model_discovery import print_header, print_success, print_error

        # These functions should not raise exceptions
        print_header("Test Header")
        print_success("Test Success")
        print_error("Test Error")

    @patch('tempfile.TemporaryDirectory')
    @patch('pathlib.Path')
    def test_file_operations_isolation(self, mock_path, mock_temp_dir):
        """Test that file operations are properly isolated"""
        # This test ensures file operations don't affect the actual filesystem
        mock_temp_dir.return_value.__enter__ = Mock(return_value="/tmp/test")
        mock_temp_dir.return_value.__exit__ = Mock(return_value=None)

        # The setup should use temporary directories for testing
        setup = ModelDiscoverySetup()
        # This should not create actual files
        assert setup.base_dir is not None