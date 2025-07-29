#!/usr/bin/env python3
"""
AI System Installer Creator
Creates executable installers for Windows, macOS, and Linux
"""

import os
import sys
import shutil
import subprocess
import platform
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional
import json

class InstallerCreator:
    """Creates installation packages for different platforms."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.version = "1.0.0"
        self.app_name = "AI-System"
        
    def setup_build_environment(self):
        """Setup build directories and environment."""
        print("Setting up build environment...")
        
        # Clean and create build directories
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            
        self.build_dir.mkdir(parents=True)
        self.dist_dir.mkdir(parents=True)
        
        # Create platform-specific directories
        (self.dist_dir / "windows").mkdir()
        (self.dist_dir / "linux").mkdir()
        (self.dist_dir / "macos").mkdir()
        
        print("✅ Build environment ready")
        
    def install_build_dependencies(self):
        """Install required build dependencies."""
        print("Installing build dependencies...")
        
        dependencies = [
            "pyinstaller>=6.0.0",
            "nsis>=3.0.0",  # For Windows NSIS installer
            "cx_Freeze>=6.15.0",  # Alternative packager
            "auto-py-to-exe>=2.40.0",  # GUI for PyInstaller
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                             check=True, capture_output=True)
                print(f"✅ Installed {dep}")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not install {dep} (may not be available on this platform)")
                
    def create_pyinstaller_spec(self) -> str:
        """Create PyInstaller spec file."""
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('config/*', 'config'),
        ('data/*', 'data'),
        ('docs/*', 'docs'),
        ('requirements/*', 'requirements'),
        ('src/ui/templates/*', 'ui/templates'),
        ('src/ui/static/*', 'ui/static'),
        ('drivers/*', 'drivers'),
        ('monitoring/*', 'monitoring'),
    ],
    hiddenimports=[
        'asyncio',
        'uvloop',
        'aiohttp',
        'torch',
        'transformers',
        'sentence_transformers',
        'chromadb',
        'langchain',
        'openai',
        'psutil',
        'GPUtil',
        'pyaudio',
        'pyttsx3',
        'speech_recognition',
        'scikit-learn',
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'cryptography',
        'redis',
        'sqlite3',
        'json',
        'yaml',
        'toml',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{self.app_name}',
)
'''
        
        spec_file = self.project_root / f"{self.app_name}.spec"
        with open(spec_file, 'w') as f:
            f.write(spec_content)
            
        return str(spec_file)
        
    def create_windows_installer(self):
        """Create Windows executable and installer."""
        print("Creating Windows installer...")
        
        try:
            # Create PyInstaller spec
            spec_file = self.create_pyinstaller_spec()
            
            # Build executable with PyInstaller
            cmd = [sys.executable, "-m", "PyInstaller", "--clean", spec_file]
            subprocess.run(cmd, check=True, cwd=self.project_root)
            
            # Move built files to dist/windows
            built_dir = self.project_root / "dist" / self.app_name
            if built_dir.exists():
                shutil.move(str(built_dir), str(self.dist_dir / "windows" / self.app_name))
                
            # Create NSIS installer script
            self.create_nsis_script()
            
            # Create ZIP package
            self.create_zip_package("windows")
            
            print("✅ Windows installer created successfully")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating Windows installer: {e}")
            
    def create_nsis_script(self):
        """Create NSIS installer script for Windows."""
        nsis_script = f'''
; AI System NSIS Installer Script

!define APPNAME "{self.app_name}"
!define COMPANYNAME "AI System Team"
!define DESCRIPTION "Comprehensive Multi-Agent AI System"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0
!define HELPURL "https://github.com/ai-system/ai-system"
!define UPDATEURL "https://github.com/ai-system/ai-system/releases"
!define ABOUTURL "https://github.com/ai-system/ai-system"
!define INSTALLSIZE 500000

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${{APPNAME}}"

Name "${{APPNAME}}"
Icon "assets\\icon.ico"
outFile "dist\\windows\\${{APPNAME}}-Setup-v${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${{If}} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${{EndIf}}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "AI System Core" SecCore
    SectionIn RO
    
    setOutPath $INSTDIR
    
    # Copy all files
    file /r "dist\\windows\\${{APPNAME}}\\*"
    
    # Create shortcuts
    createDirectory "$SMPROGRAMS\\${{APPNAME}}"
    createShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPNAME}}.exe"
    createShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPNAME}}.exe"
    
    # Registry entries
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayName" "${{APPNAME}}"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "QuietUninstallString" "$\\"$INSTDIR\\uninstall.exe$\\" /S"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "InstallLocation" "$\\"$INSTDIR$\\""
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayIcon" "$\\"$INSTDIR\\${{APPNAME}}.exe$\\""
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "HelpLink" "${{HELPURL}}"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "URLUpdateInfo" "${{UPDATEURL}}"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "URLInfoAbout" "${{ABOUTURL}}"
    writeRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "DisplayVersion" "${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}"
    writeRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "VersionMajor" ${{VERSIONMAJOR}}
    writeRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "VersionMinor" ${{VERSIONMINOR}}
    writeRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoModify" 1
    writeRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "NoRepair" 1
    writeRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}" "EstimatedSize" ${{INSTALLSIZE}}
    
    # Create uninstaller
    writeUninstaller "$INSTDIR\\uninstall.exe"
sectionEnd

section "Desktop Shortcut" SecDesktop
    createShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPNAME}}.exe"
sectionEnd

section "Start Menu Shortcuts" SecStartMenu
    createDirectory "$SMPROGRAMS\\${{APPNAME}}"
    createShortCut "$SMPROGRAMS\\${{APPNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\${{APPNAME}}.exe"
    createShortCut "$SMPROGRAMS\\${{APPNAME}}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
sectionEnd

section "Uninstall"
    # Remove shortcuts
    delete "$DESKTOP\\${{APPNAME}}.lnk"
    delete "$SMPROGRAMS\\${{APPNAME}}\\*"
    rmDir "$SMPROGRAMS\\${{APPNAME}}"
    
    # Remove files
    rmDir /r "$INSTDIR"
    
    # Remove registry entries
    deleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{APPNAME}}"
sectionEnd
'''
        
        nsis_file = self.project_root / "installer.nsi"
        with open(nsis_file, 'w') as f:
            f.write(nsis_script)
            
    def create_linux_package(self):
        """Create Linux installation package."""
        print("Creating Linux package...")
        
        try:
            # Create AppImage or DEB package
            # For now, create a tar.gz with installation script
            
            linux_dir = self.dist_dir / "linux"
            package_dir = linux_dir / f"{self.app_name}-{self.version}"
            package_dir.mkdir(parents=True)
            
            # Copy source files
            shutil.copytree("src", package_dir / "src")
            shutil.copytree("config", package_dir / "config")
            shutil.copytree("requirements", package_dir / "requirements")
            
            # Copy installation files
            shutil.copy("install.sh", package_dir / "install.sh")
            shutil.copy("setup.py", package_dir / "setup.py")
            shutil.copy("README.md", package_dir / "README.md")
            shutil.copy("LICENSE", package_dir / "LICENSE")
            
            # Make install script executable
            os.chmod(package_dir / "install.sh", 0o755)
            
            # Create tar.gz
            with tarfile.open(linux_dir / f"{self.app_name}-{self.version}-linux.tar.gz", "w:gz") as tar:
                tar.add(package_dir, arcname=f"{self.app_name}-{self.version}")
                
            print("✅ Linux package created successfully")
            
        except Exception as e:
            print(f"❌ Error creating Linux package: {e}")
            
    def create_macos_package(self):
        """Create macOS application bundle."""
        print("Creating macOS package...")
        
        try:
            macos_dir = self.dist_dir / "macos"
            app_dir = macos_dir / f"{self.app_name}.app"
            contents_dir = app_dir / "Contents"
            macos_bin_dir = contents_dir / "MacOS"
            resources_dir = contents_dir / "Resources"
            
            # Create directory structure
            macos_bin_dir.mkdir(parents=True)
            resources_dir.mkdir(parents=True)
            
            # Create Info.plist
            info_plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{self.app_name}</string>
    <key>CFBundleIdentifier</key>
    <string>com.aisystem.{self.app_name.lower()}</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleVersion</key>
    <string>{self.version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.version}</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
</dict>
</plist>'''
            
            with open(contents_dir / "Info.plist", 'w') as f:
                f.write(info_plist)
                
            # Copy application files (would use PyInstaller for actual executable)
            # For now, create a shell script launcher
            launcher_script = f'''#!/bin/bash
cd "$(dirname "$0")/../Resources"
python3 -m src.main "$@"
'''
            
            launcher_path = macos_bin_dir / self.app_name
            with open(launcher_path, 'w') as f:
                f.write(launcher_script)
            os.chmod(launcher_path, 0o755)
            
            # Copy resources
            shutil.copytree("src", resources_dir / "src")
            shutil.copytree("config", resources_dir / "config")
            
            print("✅ macOS package created successfully")
            
        except Exception as e:
            print(f"❌ Error creating macOS package: {e}")
            
    def create_zip_package(self, platform: str):
        """Create ZIP package for distribution."""
        platform_dir = self.dist_dir / platform
        zip_path = platform_dir / f"{self.app_name}-{self.version}-{platform}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(platform_dir):
                for file in files:
                    if file.endswith('.zip'):
                        continue
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(platform_dir)
                    zipf.write(file_path, arcname)
                    
    def create_universal_installer(self):
        """Create a universal installer script."""
        installer_script = '''#!/usr/bin/env python3
"""
AI System Universal Installer
Automatically detects platform and installs appropriate package
"""

import os
import sys
import platform
import subprocess
import urllib.request
import zipfile
import tarfile
from pathlib import Path

class UniversalInstaller:
    def __init__(self):
        self.system = platform.system().lower()
        self.architecture = platform.machine().lower()
        self.base_url = "https://github.com/ai-system/ai-system/releases/latest/download"
        
    def detect_platform(self):
        """Detect the current platform."""
        if self.system == "windows":
            return "windows"
        elif self.system == "darwin":
            return "macos"
        elif self.system == "linux":
            return "linux"
        else:
            raise Exception(f"Unsupported platform: {self.system}")
            
    def download_package(self, platform):
        """Download the appropriate package."""
        if platform == "windows":
            filename = "AI-System-1.0.0-windows.zip"
        elif platform == "linux":
            filename = "AI-System-1.0.0-linux.tar.gz"
        elif platform == "macos":
            filename = "AI-System-1.0.0-macos.zip"
            
        url = f"{self.base_url}/{filename}"
        print(f"Downloading {filename}...")
        
        urllib.request.urlretrieve(url, filename)
        return filename
        
    def extract_package(self, filename):
        """Extract the downloaded package."""
        print(f"Extracting {filename}...")
        
        if filename.endswith('.zip'):
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall()
        elif filename.endswith('.tar.gz'):
            with tarfile.open(filename, 'r:gz') as tar_ref:
                tar_ref.extractall()
                
    def install(self):
        """Main installation process."""
        try:
            platform = self.detect_platform()
            print(f"Detected platform: {platform}")
            
            filename = self.download_package(platform)
            self.extract_package(filename)
            
            # Run platform-specific installation
            if platform == "windows":
                print("Please run the extracted setup.exe file to complete installation.")
            elif platform == "linux":
                os.system("chmod +x install.sh && ./install.sh")
            elif platform == "macos":
                print("Please drag the AI-System.app to your Applications folder.")
                
            print("Installation completed successfully!")
            
        except Exception as e:
            print(f"Installation failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    installer = UniversalInstaller()
    installer.install()
'''
        
        with open(self.dist_dir / "install.py", 'w') as f:
            f.write(installer_script)
        os.chmod(self.dist_dir / "install.py", 0o755)
        
    def create_all_installers(self):
        """Create installers for all platforms."""
        print("Creating installers for all platforms...")
        
        self.setup_build_environment()
        self.install_build_dependencies()
        
        # Create platform-specific packages
        if platform.system() == "Windows":
            self.create_windows_installer()
        
        self.create_linux_package()
        self.create_macos_package()
        self.create_universal_installer()
        
        # Create checksums
        self.create_checksums()
        
        print("\n✅ All installers created successfully!")
        print(f"📁 Distribution files available in: {self.dist_dir}")
        
    def create_checksums(self):
        """Create SHA256 checksums for all packages."""
        import hashlib
        
        checksums = {}
        
        for platform_dir in self.dist_dir.iterdir():
            if platform_dir.is_dir():
                for file_path in platform_dir.rglob("*"):
                    if file_path.is_file() and not file_path.name.startswith('.'):
                        with open(file_path, 'rb') as f:
                            content = f.read()
                            sha256_hash = hashlib.sha256(content).hexdigest()
                            relative_path = file_path.relative_to(self.dist_dir)
                            checksums[str(relative_path)] = sha256_hash
                            
        # Write checksums file
        with open(self.dist_dir / "checksums.txt", 'w') as f:
            for file_path, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {file_path}\n")
                
        print("✅ Checksums created")

def main():
    """Main entry point."""
    creator = InstallerCreator()
    creator.create_all_installers()

if __name__ == "__main__":
    main()