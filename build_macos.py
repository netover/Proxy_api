#!/usr/bin/env python3
"""
macOS executable build script for LLM Proxy API
Creates a standalone executable with embedded configuration
Note: Run this script on a macOS system for native build
"""

import os
import sys
import shutil
from pathlib import Path
import yaml
import time
from typing import Dict, Any

def load_build_config() -> Dict[str, Any]:
    """Load build configuration"""
    config_path = Path("build_config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Default configuration
        return {
            "app_name": "LLM Proxy API",
            "version": "1.0.0",
            "company": "Your Company",
            "description": "High-performance LLM proxy with intelligent routing",
            "console": True,
            "onefile": True,
            "include_files": [
                ("config.yaml", "config.yaml"),
                ("logs", "logs")
            ]
        }

def copy_config_with_permissions():
    """Copy config.yaml to dist directory with proper permissions"""
    print("📋 Copying config.yaml to dist directory with proper permissions...")

    source_config = Path("config.yaml")
    dist_dir = Path("dist")
    target_config = dist_dir / "config.yaml"

    if not source_config.exists():
        print("❌ Source config.yaml not found!")
        return False

    if not dist_dir.exists():
        dist_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Copy the file
        shutil.copy2(source_config, target_config)

        # Set proper permissions (executable if needed, readable by all)
        os.chmod(target_config, 0o644)  # rw-r--r--

        print(f"✅ Config file copied to: {target_config.absolute()}")
        print(f"   Permissions set to: {oct(os.stat(target_config).st_mode)}")

        return True
    except Exception as e:
        print(f"❌ Failed to copy config file: {e}")
        return False

def build_executable():
    """Build macOS executable using PyInstaller"""
    print("🚀 Building LLM Proxy API macOS executable...")

    # Load build configuration
    config = load_build_config()
    print(f"📋 Build configuration loaded: {config['app_name']} v{config['version']}")

    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)

    # Prepare PyInstaller command for macOS
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        f"--name={config['app_name'].replace(' ', '_')}",
        "--onefile",
        "--console",
        # Core framework imports - COMPREHENSIVE UVICORN IMPORTS
        "--hidden-import=uvicorn",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.loops.uvloop",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.http.httptools_impl",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=uvicorn.main",
        "--hidden-import=uvicorn.config",
        "--hidden-import=uvicorn.supervisors",
        "--hidden-import=uvicorn.workers",

        # FastAPI comprehensive imports
        "--hidden-import=fastapi",
        "--hidden-import=fastapi.routing",
        "--hidden-import=fastapi.applications",
        "--hidden-import=fastapi.middleware",
        "--hidden-import=fastapi.middleware.cors",
        "--hidden-import=fastapi.middleware.gzip",
        "--hidden-import=fastapi.middleware.trustedhost",
        "--hidden-import=fastapi.middleware.httpsredirect",
        "--hidden-import=fastapi.security",
        "--hidden-import=fastapi.security.api_key",
        "--hidden-import=fastapi.security.http",
        "--hidden-import=fastapi.security.oauth2",
        "--hidden-import=fastapi.security.open_id_connect",
        "--hidden-import=fastapi.openapi",
        "--hidden-import=fastapi.openapi.docs",
        "--hidden-import=fastapi.openapi.utils",
        "--hidden-import=fastapi.dependencies",
        "--hidden-import=fastapi.dependencies.utils",
        "--hidden-import=fastapi.dependencies.models",
        "--hidden-import=fastapi.encoders",
        "--hidden-import=fastapi.exceptions",
        "--hidden-import=fastapi.params",
        "--hidden-import=fastapi.requests",
        "--hidden-import=fastapi.responses",
        "--hidden-import=fastapi.staticfiles",
        "--hidden-import=fastapi.templating",
        "--hidden-import=fastapi.testclient",
        "--hidden-import=fastapi.utils",

        # Data validation - COMPREHENSIVE PYDANTIC
        "--hidden-import=pydantic",
        "--hidden-import=pydantic.fields",
        "--hidden-import=pydantic.main",
        "--hidden-import=pydantic.types",
        "--hidden-import=pydantic_settings",
        "--hidden-import=pydantic_settings.sources",
        "--hidden-import=pydantic_core",
        "--hidden-import=pydantic_core.core_schema",

        # HTTP client - COMPREHENSIVE HTTPX
        "--hidden-import=httpx",
        "--hidden-import=httpx._main",
        "--hidden-import=httpx._config",
        "--hidden-import=httpx._client",
        "--hidden-import=httpx._transports",
        "--hidden-import=httpx._utils",
        "--hidden-import=httpx._exceptions",
        "--hidden-import=httpx._models",
        "--hidden-import=httpx._urls",
        "--hidden-import=httpx._auth",
        "--hidden-import=httpx._decoders",
        "--hidden-import=httpx._multipart",
        "--hidden-import=httpx._sync",
        "--hidden-import=httpx._async",
        "--hidden-import=httpx._api",

        # Async libraries - CRITICAL FOR STREAMING
        "--hidden-import=anyio",
        "--hidden-import=anyio._core",
        "--hidden-import=anyio._backends",
        "--hidden-import=anyio._backends.asyncio",
        "--hidden-import=anyio.abc",
        "--hidden-import=anyio.streams",
        "--hidden-import=anyio.to_thread",
        "--hidden-import=anyio.from_thread",

        # Performance optimizations
        "--hidden-import=uvloop",  # Linux/macOS only
        "--hidden-import=orjson",

        # Rate limiting - COMPREHENSIVE SLOWAPI
        "--hidden-import=slowapi",
        "--hidden-import=slowapi.middleware",
        "--hidden-import=slowapi.util",
        "--hidden-import=slowapi.errors",
        "--hidden-import=slowapi.storage",
        "--hidden-import=slowapi.storage.redis",
        "--hidden-import=slowapi.storage.memcached",
        "--hidden-import=slowapi.storage.memory",
        "--hidden-import=slowapi.wrappers",

        # Configuration and utilities
        "--hidden-import=pyyaml",
        "--hidden-import=json",
        "--hidden-import=jwt",
        "--hidden-import=pyasn1",
        "--hidden-import=cryptography",
        "--hidden-import=cryptography.hazmat",
        "--hidden-import=cryptography.hazmat.primitives",
        "--hidden-import=cryptography.hazmat.backends",

        # Project modules - ALL CORE MODULES
        "--hidden-import=src.core.config",
        "--hidden-import=src.core.logging",
        "--hidden-import=src.core.app_config",
        "--hidden-import=src.core.metrics",
        "--hidden-import=src.core.auth",
        "--hidden-import=src.core.circuit_breaker",
        "--hidden-import=src.core.unified_config",
        "--hidden-import=src.core.provider_factory",
        "--hidden-import=src.core.exceptions",
        "--hidden-import=src.core.rate_limiter",
        "--hidden-import=src.core.smart_cache",
        "--hidden-import=src.core.http_client",
        "--hidden-import=src.core.memory_manager",
        "--hidden-import=src.core.app_state",
        "--hidden-import=src.services.provider_loader",
        "--hidden-import=src.models.requests",
        "--hidden-import=src.models.responses",
        "--hidden-import=src.utils.context_condenser",
        "--hidden-import=src.utils.helpers",
        "--hidden-import=src.config.models",

        # All provider modules
        "--hidden-import=src.providers.base",
        "--hidden-import=src.providers.openai",
        "--hidden-import=src.providers.anthropic",
        "--hidden-import=src.providers.cohere",
        "--hidden-import=src.providers.perplexity",
        "--hidden-import=src.providers.grok",
        "--hidden-import=src.providers.blackbox",
        "--hidden-import=src.providers.openrouter",
        "--hidden-import=src.providers.azure_openai",
        "--hidden-import=src.providers.dynamic_base",
        "--hidden-import=src.providers.dynamic_blackbox",

        # Collect all for complex packages - ENHANCED
        "--collect-all=fastapi",
        "--collect-all=pydantic",
        "--collect-all=httpx",
        "--collect-all=uvicorn",
        "--collect-all=uvloop",
        "--collect-all=orjson",
        "--collect-all=anyio",
        "--collect-all=slowapi",
        "--collect-all=pyyaml",
        "--collect-all=cryptography"
    ]

    # Add include files
    for src, dst in config.get("include_files", []):
        src_path = Path(src)
        if src_path.exists():
            cmd.append(f"--add-data={src_path}:{dst}")

    # Add main script
    cmd.append("main.py")

    print(f"🔧 PyInstaller command: {' '.join(cmd)}")

    # Run PyInstaller
    try:
        print("🏗️  Running PyInstaller...")
        start_time = time.time()

        import subprocess
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode != 0:
            print("❌ PyInstaller failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

        build_time = time.time() - start_time
        print(f"✅ Build completed in {build_time:.2f} seconds")
        # Check if executable was created
        exe_name = f"{config['app_name'].replace(' ', '_')}"
        exe_path = dist_dir / exe_name

        if exe_path.exists():
            exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(f"📦 Executable size: {exe_size:.2f} MB")
            print(f"📁 Executable location: {exe_path.absolute()}")

            # Copy config file with proper permissions
            if copy_config_with_permissions():
                # Make executable
                os.chmod(exe_path, 0o755)
                print(f"🔧 Executable permissions set to 755")
                return True
            else:
                print("⚠️  Executable built but config file copy failed")
                return False
        else:
            print("❌ Executable not found after build!")
            return False

    except Exception as e:
        print(f"❌ Build failed with exception: {e}")
        return False

def main():
    """Main build function"""
    print("🔨 LLM Proxy API macOS Build Script")
    print("=" * 40)

    # Build executable
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)

    print("\n✅ Build completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the executable: ./dist/llm-proxy-api")
    print("2. Configure your API keys in the embedded config.yaml")
    print("3. Run the executable to start the proxy server")

if __name__ == "__main__":
    main()