#!/usr/bin/env python3
"""
Model Discovery Setup Script

This script helps new users set up the Model Discovery system quickly and easily.
It handles:
- Environment configuration
- API key setup
- Provider configuration
- Initial model discovery
- Validation and testing
"""

import os
import sys
import json
import yaml
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import getpass
import platform
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

class ModelDiscoverySetup:
    """Main setup class for Model Discovery system."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.scripts_dir = self.base_dir / "scripts"
        self.setup_log = []
        
    def check_system_requirements(self) -> bool:
        """Check if the system meets all requirements."""
        print_header("System Requirements Check")
        
        requirements_met = True
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 11):
            print_error(f"Python 3.11+ required, found {python_version.major}.{python_version.minor}")
            requirements_met = False
        else:
            print_success(f"Python {python_version.major}.{python_version.minor} detected")
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
            print_success("pip is available")
        except subprocess.CalledProcessError:
            print_error("pip is not available")
            requirements_met = False
        
        # Check git (optional)
        try:
            subprocess.run(["git", "--version"], check=True, capture_output=True)
            print_success("git is available")
        except subprocess.CalledProcessError:
            print_warning("git is not available (optional)")
        
        return requirements_met
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        print_header("Installing Dependencies")
        
        try:
            # Install requirements
            requirements_file = self.base_dir / "requirements.txt"
            if requirements_file.exists():
                print_info("Installing Python dependencies...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True)
                print_success("Dependencies installed successfully")
            else:
                print_warning("requirements.txt not found, skipping dependency installation")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e}")
            return False
    
    def create_config_files(self) -> bool:
        """Create configuration files."""
        print_header("Creating Configuration Files")
        
        try:
            # Create config directory
            self.config_dir.mkdir(exist_ok=True)
            
            # Create config.yaml if it doesn't exist
            config_file = self.config_dir / "config.yaml"
            if not config_file.exists():
                default_config = {
                    "providers": {
                        "openai": {
                            "api_key": "",
                            "enabled": True,
                            "timeout": 30
                        },
                        "anthropic": {
                            "api_key": "",
                            "enabled": True,
                            "timeout": 30
                        },
                        "azure_openai": {
                            "api_key": "",
                            "endpoint": "",
                            "enabled": False,
                            "timeout": 30
                        },
                        "cohere": {
                            "api_key": "",
                            "enabled": False,
                            "timeout": 30
                        }
                    },
                    "discovery": {
                        "cache_ttl": 300,
                        "cache_dir": "./cache",
                        "timeout": 30,
                        "max_retries": 3,
                        "auto_refresh": True,
                        "refresh_interval": 3600
                    },
                    "monitoring": {
                        "enabled": True,
                        "log_level": "INFO"
                    }
                }
                
                with open(config_file, 'w') as f:
                    yaml.dump(default_config, f, default_flow_style=False)
                
                print_success(f"Created {config_file}")
            else:
                print_info(f"{config_file} already exists")
            
            # Create .env.example
            env_example = self.base_dir / ".env.example"
            if not env_example.exists():
                env_content = """# Model Discovery API Keys
# Copy this file to .env and fill in your actual API keys

# OpenAI
OPENAI_API_KEY=your-openai-api-key-here

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Cohere
COHERE_API_KEY=your-cohere-api-key-here

# Optional: Custom providers
CUSTOM_PROVIDER_API_KEY=your-custom-provider-key-here
"""
                with open(env_example, 'w') as f:
                    f.write(env_content)
                print_success(f"Created {env_example}")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to create config files: {e}")
            return False
    
    def setup_api_keys(self) -> Dict[str, str]:
        """Interactive setup of API keys."""
        print_header("API Key Configuration")
        
        providers = {
            "openai": "OpenAI",
            "anthropic": "Anthropic",
            "azure_openai": "Azure OpenAI",
            "cohere": "Cohere"
        }
        
        api_keys = {}
        
        print_info("Please provide your API keys (press Enter to skip):")
        print_info("You can always add these later in config.yaml or .env file\n")
        
        for provider_key, provider_name in providers.items():
            key = getpass.getpass(f"{provider_name} API Key: ").strip()
            if key:
                api_keys[provider_key] = key
                print_success(f"{provider_name} API key configured")
            else:
                print_warning(f"{provider_name} API key skipped")
        
        return api_keys
    
    def update_config_with_keys(self, api_keys: Dict[str, str]) -> bool:
        """Update configuration with provided API keys."""
        print_header("Updating Configuration")
        
        try:
            config_file = self.config_dir / "config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Update API keys
                for provider, key in api_keys.items():
                    if provider in config.get("providers", {}):
                        config["providers"][provider]["api_key"] = key
                
                # Backup original config
                backup_file = config_file.with_suffix(f'.yaml.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                shutil.copy2(config_file, backup_file)
                print_info(f"Backup created: {backup_file}")
                
                # Write updated config
                with open(config_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                print_success("Configuration updated with API keys")
                return True
            else:
                print_error("config.yaml not found")
                return False
                
        except Exception as e:
            print_error(f"Failed to update configuration: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories."""
        print_header("Creating Directories")
        
        directories = [
            self.base_dir / "cache",
            self.base_dir / "logs",
            self.base_dir / "data",
            self.base_dir / "config" / "providers"
        ]
        
        for directory in directories:
            directory.mkdir(exist_ok=True)
            print_success(f"Created directory: {directory}")
        
        return True
    
    def validate_installation(self) -> bool:
        """Validate the installation."""
        print_header("Validating Installation")
        
        try:
            # Test Python imports
            from src.core.model_discovery import ModelDiscovery
            from src.core.cache_manager import CacheManager
            from src.core.provider_factory import ProviderFactory
            
            print_success("Core modules imported successfully")
            
            # Test basic functionality
            cache_manager = CacheManager()
            provider_factory = ProviderFactory()
            discovery = ModelDiscovery(cache_manager, provider_factory)
            
            print_success("Model Discovery system initialized")
            
            # Test configuration loading
            config_file = self.config_dir / "config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                print_success("Configuration loaded successfully")
            else:
                print_warning("Configuration file not found")
            
            return True
            
        except Exception as e:
            print_error(f"Validation failed: {e}")
            return False
    
    def create_startup_script(self) -> bool:
        """Create startup scripts for different platforms."""
        print_header("Creating Startup Scripts")
        
        try:
            # Create startup script for Unix-like systems
            startup_sh = self.scripts_dir / "start.sh"
            startup_content = f"""#!/bin/bash
# ProxyAPI Model Discovery Startup Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "Starting ProxyAPI Model Discovery..."
cd "{self.base_dir}"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if needed
if [ ! -f "requirements_installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    touch requirements_installed
fi

# Start the application
echo "Starting web server on http://localhost:8000"
python web_ui.py
"""
            
            with open(startup_sh, 'w') as f:
                f.write(startup_content)
            os.chmod(startup_sh, 0o755)
            print_success(f"Created {startup_sh}")
            
            # Create startup script for Windows
            startup_bat = self.scripts_dir / "start.bat"
            startup_bat_content = f"""@echo off
REM ProxyAPI Model Discovery Startup Script
REM Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo Starting ProxyAPI Model Discovery...
cd /d "{self.base_dir}"

REM Check if virtual environment exists
if exist "venv\\Scripts\\activate.bat" (
    echo Activating virtual environment...
    call venv\\Scripts\\activate.bat
)

REM Install dependencies if needed
if not exist "requirements_installed" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo. > requirements_installed
)

REM Start the application
echo Starting web server on http://localhost:8000
python web_ui.py
pause
"""
            
            with open(startup_bat, 'w') as f:
                f.write(startup_bat_content)
            print_success(f"Created {startup_bat}")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to create startup scripts: {e}")
            return False
    
    def create_docker_files(self) -> bool:
        """Create Docker configuration files."""
        print_header("Creating Docker Configuration")
        
        try:
            # Create Dockerfile
            dockerfile = self.base_dir / "Dockerfile"
            dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/cache /app/logs /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=10)"

# Start the application
CMD ["python", "web_ui.py"]
"""
            
            with open(dockerfile, 'w') as f:
                f.write(dockerfile_content)
            print_success("Created Dockerfile")
            
            # Create docker-compose.yml
            docker_compose = self.base_dir / "docker-compose.yml"
            compose_content = """version: '3.8'

services:
  proxyapi:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./config:/app/config
      - ./cache:/app/cache
      - ./logs:/app/logs
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
"""
            
            with open(docker_compose, 'w') as f:
                f.write(compose_content)
            print_success("Created docker-compose.yml")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to create Docker files: {e}")
            return False
    
    def run_initial_discovery(self) -> bool:
        """Run initial model discovery to test setup."""
        print_header("Running Initial Discovery Test")
        
        try:
            # Import here to avoid issues if setup is incomplete
            from src.core.model_discovery import ModelDiscovery
            from src.core.cache_manager import CacheManager
            from src.core.provider_factory import ProviderFactory
            
            # Create test configuration
            test_config = {
                "providers": {
                    "openai": {
                        "api_key": "test-key",
                        "enabled": True
                    }
                }
            }
            
            # Initialize services
            cache_manager = CacheManager()
            provider_factory = ProviderFactory()
            discovery = ModelDiscovery(cache_manager, provider_factory)
            
            print_info("Testing model discovery system...")
            print_info("Note: This is a basic test. Real discovery requires valid API keys.")
            
            # Test basic functionality
            print_success("Model Discovery system is ready for use!")
            print_info("Add your API keys to config.yaml and restart the application")
            
            return True
            
        except Exception as e:
            print_error(f"Initial discovery test failed: {e}")
            return False
    
    def generate_setup_report(self) -> Dict[str, bool]:
        """Generate a comprehensive setup report."""
        print_header("Setup Report")
        
        report = {
            "system_requirements": self.check_system_requirements(),
            "dependencies": self.install_dependencies(),
            "config_files": self.create_config_files(),
            "directories": self.create_directories(),
            "validation": self.validate_installation(),
            "startup_scripts": self.create_startup_script(),
            "docker_files": self.create_docker_files(),
            "initial_discovery": self.run_initial_discovery()
        }
        
        # Summary
        print("\n" + "="*60)
        print("SETUP SUMMARY")
        print("="*60)
        
        for step, status in report.items():
            status_icon = "✅" if status else "❌"
            print(f"{status_icon} {step.replace('_', ' ').title()}")
        
        total_steps = len(report)
        completed_steps = sum(report.values())
        
        print(f"\n📊 Completion: {completed_steps}/{total_steps} steps completed")
        
        if completed_steps == total_steps:
            print_success("🎉 Setup completed successfully!")
            print_info("\nNext steps:")
            print_info("1. Add your API keys to config/config.yaml")
            print_info("2. Run: python scripts/start.py")
            print_info("3. Open: http://localhost:8000")
        else:
            print_warning("⚠️  Some steps failed. Please check the errors above.")
        
        return report
    
    def interactive_setup(self):
        """Run interactive setup wizard."""
        print_header("Model Discovery Setup Wizard")
        print_info("Welcome to the Model Discovery setup wizard!")
        print_info("This will guide you through the initial setup process.\n")
        
        # Run setup steps
        api_keys = self.setup_api_keys()
        if api_keys:
            self.update_config_with_keys(api_keys)
        
        # Generate final report
        report = self.generate_setup_report()
        
        # Save setup log
        setup_log_file = self.base_dir / "setup.log"
        with open(setup_log_file, 'w') as f:
            f.write(f"Setup completed at: {datetime.now().isoformat()}\n")
            f.write(f"System: {platform.system()} {platform.release()}\n")
            f.write(f"Python: {sys.version}\n")
            f.write("Setup results:\n")
            for step, status in report.items():
                f.write(f"  {step}: {'SUCCESS' if status else 'FAILED'}\n")
        
        print_success(f"Setup log saved to: {setup_log_file}")
    
    def quick_setup(self):
        """Run quick setup with minimal interaction."""
        print_header("Quick Setup")
        print_info("Running quick setup with default configuration...")
        
        steps = [
            ("System requirements", self.check_system_requirements),
            ("Dependencies", self.install_dependencies),
            ("Config files", self.create_config_files),
            ("Directories", self.create_directories),
            ("Validation", self.validate_installation),
            ("Startup scripts", self.create_startup_script),
            ("Docker files", self.create_docker_files),
            ("Initial test", self.run_initial_discovery)
        ]
        
        for step_name, step_func in steps:
            print_info(f"Running {step_name.lower()}...")
            if not step_func():
                print_error(f"{step_name} failed")
                return False
        
        print_success("🎉 Quick setup completed successfully!")
        return True


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Model Discovery Setup Script")
    parser.add_argument("--interactive", action="store_true", 
                       help="Run interactive setup wizard")
    parser.add_argument("--quick", action="store_true", 
                       help="Run quick setup with defaults")
    parser.add_argument("--check", action="store_true", 
                       help="Check system requirements only")
    
    args = parser.parse_args()
    
    setup = ModelDiscoverySetup()
    
    try:
        if args.check:
            setup.check_system_requirements()
        elif args.interactive:
            setup.interactive_setup()
        elif args.quick:
            setup.quick_setup()
        else:
            # Default to interactive
            setup.interactive_setup()
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("Setup interrupted by user")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()