#!/usr/bin/env python3
"""
Build script for LLM Proxy API
This script handles building the application for different platforms
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("Dependencies installed successfully!")

def build_executable():
    """Build executable using PyInstaller"""
    print("Building executable...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "LLM_Proxy_API",
        "--clean",
        "build.spec"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        return False

def build_docker():
    """Build Docker image"""
    print("Building Docker image...")
    
    try:
        subprocess.run(["docker", "build", "-t", "llm-proxy-api:latest", "."], check=True)
        print("Docker image built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Docker build failed: {e}")
        return False

def main():
    """Main build function"""
    print(f"Building LLM Proxy API on {platform.system()} {platform.release()}")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Build options
    build_exec = "--no-exec" not in sys.argv
    build_dock = "--no-docker" not in sys.argv
    
    success = True
    
    # Build executable
    if build_exec:
        if not build_executable():
            success = False
    
    # Build Docker image
    if build_dock:
        if not build_docker():
            success = False
    
    if success:
        print("\nBuild completed successfully!")
        if build_exec and os.path.exists("dist/LLM_Proxy_API.exe"):
            print(f"Executable located at: {os.path.abspath('dist/LLM_Proxy_API.exe')}")
        if build_dock:
            print("Docker image: llm-proxy-api:latest")
    else:
        print("\nBuild completed with errors!")
        sys.exit(1)

if __name__ == "__main__":
    main()
