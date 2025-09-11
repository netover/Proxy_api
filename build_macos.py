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
        # Core framework imports
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.http.h11_impl",
        "--hidden-import=uvicorn.protocols.http.httptools_impl",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=fastapi",
        "--hidden-import=fastapi.routing",
        "--hidden-import=fastapi.applications",
        "--hidden-import=fastapi.middleware",
        "--hidden-import=fastapi.middleware.cors",
        "--hidden-import=fastapi.middleware.gzip",

        # Data validation
        "--hidden-import=pydantic",
        "--hidden-import=pydantic.fields",
        "--hidden-import=pydantic.main",
        "--hidden-import=pydantic.types",
        "--hidden-import=pydantic_settings",

        # HTTP client
        "--hidden-import=httpx",
        "--hidden-import=httpx._main",
        "--hidden-import=httpx._config",
        "--hidden-import=httpx._client",
        "--hidden-import=httpx._transports",
        "--hidden-import=httpx._utils",

        # Performance optimizations
        "--hidden-import=uvloop",  # Linux/macOS only
        "--hidden-import=orjson",

        # Configuration and utilities
        "--hidden-import=pyyaml",
        "--hidden-import=slowapi",
        "--hidden-import=jwt",
        "--hidden-import=pyasn1",

        # Project modules
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
        "--hidden-import=src.providers.base",
        "--hidden-import=src.providers.openai",
        "--hidden-import=src.providers.anthropic",
        "--hidden-import=src.providers.dynamic_base",
        "--hidden-import=src.providers.dynamic_blackbox",
        "--hidden-import=src.services.provider_loader",
        "--hidden-import=src.models.requests",

        # Collect all for complex packages
        "--collect-all=fastapi",
        "--collect-all=pydantic",
        "--collect-all=httpx",
        "--collect-all=uvicorn",
        "--collect-all=uvloop",
        "--collect-all=orjson"
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