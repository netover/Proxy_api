#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path

def run_build():
    # Configure paths
    project_root = Path(__file__).parent.resolve()
    spec_path = project_root / "LLM_Proxy_API.spec"
    output_dir = project_root / "dist"
    work_dir = project_root / "build"

    # Ensure directories exist
    output_dir.mkdir(exist_ok=True)
    work_dir.mkdir(exist_ok=True)

    # PyInstaller command
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--log-level=INFO",
        "--workpath=" + str(work_dir),
        "--distpath=" + str(output_dir),
        str(spec_path),
    ]

    print("Building with command:")
    print(" ".join(cmd))

    try:
        subprocess.check_call(cmd)
        print("\nBuild completed successfully!")
        print(f"Output in: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        return False

if __name__ == "__main__":
    if not run_build():
        print("Build process terminated successfully.")
