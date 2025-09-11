#!/usr/bin/env python3
import os
import sys
import subprocess
import platform

def main():
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])
        import PyInstaller

    # Check Python version
    if sys.version_info < (3, 12):
        print("Warning: Python 3.12 or higher recommended")
        print(f"Detected Python version: {sys.version}")

    # Get platform-specific settings
    target_system = platform.system()
    if target_system == "Windows":
        exe_suffix = ".exe"
        paths = ["C:\\Windows\\System32", "C:\\Users\\User"]
        # Create directory structure
        os.makedirs("build\\windows", exist_ok=True)
    elif target_system == "Darwin":
        exe_suffix = ""
        paths = ["/usr/local/bin", "/Applications"]
        os.makedirs("build/macos", exist_ok=True)
    else:  # Linux
        exe_suffix = ""
        paths = ["/usr/bin", "/usr/local/bin"]
        os.makedirs("build/linux", exist_ok=True)

    # Build application
    print(f"Building LLM_Proxy_API for {target_system}")
    try:
        build_cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--_clean",
            "--log-level=INFO",
            "--additional-hooks-dir=hooks",
            "--workpath=buildPyInstaller",
            "--distpath=distPyInstaller",
            "main.py"
        ]
        if target_system == "Windows":
            build_cmd.extend(["--win-private-assemblies"])
            build_cmd.extend(["--uac-admin"])
        else:
            build_cmd.extend(["--add-data", "config:."])

        subprocess.check_call(build_cmd)
        print("Build successful!")

        # Test the executable
        exe_path = f"./distPyInstaller/LLM_Proxy_API{exe_suffix}"
        if os.path.exists(exe_path):
            print(f"Testing {exe_path}...")
            test_cmd = [exe_path]
            for path in paths:
                try:
                    subprocess.check_call(test_cmd, cwd=path)
                    print(f"Test successful in {path}")
                    break
                except subprocess.CalledProcessError as e:
                    print(f"Test failed in {path}: {e}")
        else:
            print(f"Cannot find executable at {exe_path}")

    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
