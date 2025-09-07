#!/usr/bin/env python3
"""
Windows executable build script for LLM Proxy API
Creates a standalone executable with embedded configuration
"""

import os
import sys
import shutil
import subprocess
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
            "icon": "icon.ico",
            "console": True,
            "onefile": True,
            "include_files": [
                ("config.yaml", "config.yaml"),
                ("logs", "logs")
            ]
        }

def create_version_info(config: Dict[str, Any]) -> str:
    """Create version info file for Windows executable"""
    version_parts = config["version"].split(".")
    while len(version_parts) < 4:
        version_parts.append("0")

    version_info = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({version_parts[0]}, {version_parts[1]}, {version_parts[2]}, {version_parts[3]}),
    prodvers=({version_parts[0]}, {version_parts[1]}, {version_parts[2]}, {version_parts[3]}),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{config["company"]}'),
        StringStruct(u'FileDescription', u'{config["description"]}'),
        StringStruct(u'FileVersion', u'{config["version"]}'),
        StringStruct(u'InternalName', u'llm-proxy-api'),
        StringStruct(u'LegalCopyright', u'© {config["company"]}. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'llm-proxy-api.exe'),
        StringStruct(u'ProductName', u'{config["app_name"]}'),
        StringStruct(u'ProductVersion', u'{config["version"]}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    return version_info

def build_executable():
    """Build Windows executable using PyInstaller"""
    print("🚀 Building LLM Proxy API Windows executable...")

    # Load build configuration
    config = load_build_config()
    print(f"📋 Build configuration loaded: {config['app_name']} v{config['version']}")

    # Create build directory
    build_dir = Path("build")
    dist_dir = Path("dist")
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)

    # Create version info file
    version_info_content = create_version_info(config)
    version_file = build_dir / "version_info.py"
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    print(f"📝 Version info file created: {version_file}")

    # Prepare PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        f"--name={config['app_name'].replace(' ', '_')}",
        f"--version-file={version_file}",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=fastapi",
        "--hidden-import=pydantic",
        "--hidden-import=httpx",
        "--hidden-import=pyyaml",
        "--hidden-import=structlog",
        "--hidden-import=slowapi",
        "--collect-all=fastapi",
        "--collect-all=pydantic",
        "--collect-all=httpx"
    ]

    # Add console mode
    if config.get("console", True):
        cmd.append("--console")
    else:
        cmd.append("--noconsole")

    # Add onefile mode
    if config.get("onefile", True):
        cmd.append("--onefile")

    # Add icon if exists
    icon_path = Path(config.get("icon", "icon.ico"))
    if icon_path.exists():
        cmd.append(f"--icon={icon_path}")

    # Add include files
    for src, dst in config.get("include_files", []):
        src_path = Path(src)
        if src_path.exists():
            if src_path.is_file():
                cmd.append(f"--add-data={src_path};{dst}")
            else:
                cmd.append(f"--add-data={src_path};{dst}")

    # Add main script
    cmd.append("main.py")

    print(f"🔧 PyInstaller command: {' '.join(cmd)}")

    # Run PyInstaller
    try:
        print("🏗️  Running PyInstaller...")
        start_time = time.time()

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path.cwd())

        if result.returncode != 0:
            print("❌ PyInstaller failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

        build_time = time.time() - start_time
        print(".2f"
        # Check if executable was created
        exe_name = f"{config['app_name'].replace(' ', '_')}.exe"
        exe_path = dist_dir / exe_name

        if exe_path.exists():
            exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
            print(".2f"            print(f"📁 Executable location: {exe_path.absolute()}")
            return True
        else:
            print("❌ Executable not found after build!")
            return False

    except Exception as e:
        print(f"❌ Build failed with exception: {e}")
        return False

def create_installer():
    """Create Windows installer using NSIS (optional)"""
    print("📦 Creating Windows installer...")

    # Check if makensis is available
    try:
        result = subprocess.run(["makensis", "/VERSION"], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  NSIS not found. Skipping installer creation.")
            print("   Install NSIS from https://nsis.sourceforge.io/ to create installers.")
            return False
    except FileNotFoundError:
        print("⚠️  NSIS not found. Skipping installer creation.")
        return False

    # Create NSIS script
    nsis_script = create_nsis_script()
    nsis_file = Path("installer.nsi")

    with open(nsis_file, 'w', encoding='utf-8') as f:
        f.write(nsis_script)

    # Run NSIS
    try:
        cmd = ["makensis", str(nsis_file)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Installer created successfully!")
            return True
        else:
            print("❌ Installer creation failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"❌ Installer creation failed with exception: {e}")
        return False

def create_nsis_script() -> str:
    """Create NSIS installer script"""
    config = load_build_config()

    script = f'''!include "MUI2.nsh"

Name "{config['app_name']}"
OutFile "{config['app_name'].replace(' ', '_')}_installer.exe"
Unicode True
InstallDir "$PROGRAMFILES\\{config['company']}\\{config['app_name']}"
InstallDirRegKey HKCU "Software\\{config['company']}\\{config['app_name']}" ""

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    File "dist\\{config['app_name'].replace(' ', '_')}.exe"
    File "config.yaml"
    File "README.md"

    CreateShortCut "$SMPROGRAMS\\{config['app_name']}.lnk" "$INSTDIR\\{config['app_name'].replace(' ', '_')}.exe"

    WriteRegStr HKCU "Software\\{config['company']}\\{config['app_name']}" "" $INSTDIR
    WriteUninstaller "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\{config['app_name'].replace(' ', '_')}.exe"
    Delete "$INSTDIR\\config.yaml"
    Delete "$INSTDIR\\README.md"
    Delete "$INSTDIR\\Uninstall.exe"

    Delete "$SMPROGRAMS\\{config['app_name']}.lnk"

    RMDir "$INSTDIR"

    DeleteRegKey HKCU "Software\\{config['company']}\\{config['app_name']}"
SectionEnd
'''
    return script

def main():
    """Main build function"""
    print("🔨 LLM Proxy API Build Script")
    print("=" * 40)

    # Build executable
    if not build_executable():
        print("❌ Build failed!")
        sys.exit(1)

    # Create installer (optional)
    create_installer()

    print("\n✅ Build completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the executable: .\\dist\\llm-proxy-api.exe")
    print("2. Configure your API keys in the embedded config.yaml")
    print("3. Run the executable to start the proxy server")

if __name__ == "__main__":
    main()
