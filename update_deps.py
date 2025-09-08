#!/usr/bin/env python3
"""
Dependency update script for LLM Proxy API
Updates dependencies and runs tests to verify compatibility
Also addresses security vulnerabilities and dependency conflicts
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        print(f"Command succeeded")
        return True
    except Exception as e:
        print(f"Command failed with exception: {e}")
        return False

def upgrade_pip():
    """Upgrade pip to latest version"""
    print("⬆️  Upgrading pip...")
    return run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])

def install_requirements():
    """Install dependencies from requirements.txt"""
    print("📦 Installing requirements...")
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def check_dependencies():
    """Check for dependency conflicts"""
    print("🔍 Checking for dependency conflicts...")
    return run_command([sys.executable, "-m", "pip", "check"])

def audit_vulnerabilities():
    """Audit for security vulnerabilities"""
    print("🛡️  Auditing for security vulnerabilities...")
    # Try to use pip-audit if available
    try:
        result = subprocess.run([sys.executable, "-m", "pip_audit"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Security audit completed")
            return True
        else:
            print("⚠️  pip-audit not available or found vulnerabilities")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("ℹ️  pip-audit not installed, skipping security audit")
        print("💡 Run 'pip install pip-audit' to enable security auditing")
        return True

def update_dependencies():
    """Update project dependencies"""
    print("🔄 Updating dependencies...")
    
    # Upgrade pip first
    if not upgrade_pip():
        return False
    
    # Install updated requirements
    if not install_requirements():
        return False
    
    print("✅ Dependencies updated successfully")
    return True

def run_tests():
    """Run project tests"""
    print("🧪 Running tests...")
    
    # Run tests with pytest
    if not run_command([sys.executable, "-m", "pytest", "-v"]):
        return False
    
    print("✅ All tests passed")
    return True

def main():
    """Main function"""
    print("🚀 LLM Proxy API Dependency Update Script")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Update dependencies
    if not update_dependencies():
        print("❌ Dependency update failed")
        sys.exit(1)
    
    # Check for conflicts
    if not check_dependencies():
        print("❌ Dependency conflicts detected")
        print("💡 Run 'pip check' to see details")
        sys.exit(1)
    
    # Audit for vulnerabilities
    if not audit_vulnerabilities():
        print("❌ Security vulnerabilities detected")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        sys.exit(1)
    
    print("\n✅ Dependency update, security audit, and testing completed successfully!")
    print("\n📋 Next steps:")
    print("1. Review the updated requirements.txt")
    print("2. Test the application manually")
    print("3. Commit the changes if everything works correctly")

if __name__ == "__main__":
    main()
