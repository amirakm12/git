#!/usr/bin/env python3
"""
Create Windows Executable for AI System
Uses PyInstaller to create a standalone executable
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import tempfile

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], 
                         check=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install PyInstaller: {e}")
            return False

def create_icon():
    """Create a simple icon file."""
    icon_path = Path("assets/icon.ico")
    
    # Create a simple text-based icon (for demonstration)
    # In a real scenario, you'd use a proper .ico file
    if not icon_path.exists():
        print("🎨 Creating application icon...")
        try:
            # Try to create a simple icon using PIL if available
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create a 64x64 icon
                img = Image.new('RGBA', (64, 64), (0, 100, 200, 255))
                draw = ImageDraw.Draw(img)
                
                # Draw "AI" text
                try:
                    font = ImageFont.truetype("arial.ttf", 24)
                except (OSError, IOError):
                    font = ImageFont.load_default()
                
                # Get text size and center it
                bbox = draw.textbbox((0, 0), "AI", font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (64 - text_width) // 2
                y = (64 - text_height) // 2
                
                draw.text((x, y), "AI", fill=(255, 255, 255, 255), font=font)
                
                # Save as ICO
                img.save(icon_path, format='ICO')
                print("✅ Icon created successfully")
                
            except ImportError:
                # Fallback: create a placeholder file
                with open(icon_path, 'wb') as f:
                    # Minimal ICO file header (not a real icon, but prevents errors)
                    f.write(b'\x00\x00\x01\x00\x01\x00\x10\x10\x00\x00\x01\x00\x08\x00h\x05\x00\x00\x16\x00\x00\x00')
                print("⚠️ Created placeholder icon (install Pillow for better icon)")
                
        except Exception as e:
            print(f"⚠️ Could not create icon: {e}")
            return None
            
    return str(icon_path) if icon_path.exists() else None

def create_pyinstaller_spec():
    """Create PyInstaller spec file."""
    icon_path = create_icon()
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(__file__).parent

a = Analysis(
    ['install_executable.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('config', 'config'),
        ('requirements', 'requirements'),
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('setup.py', '.'),
        {f"('{icon_path}', 'assets')" if icon_path else ""},
    ],
    hiddenimports=[
        'asyncio',
        'aiohttp',
        'uvloop',
        'psutil',
        'GPUtil',
        'torch',
        'transformers',
        'sentence_transformers',
        'chromadb',
        'langchain',
        'openai',
        'scikit_learn',
        'sklearn',
        'numpy',
        'pandas',
        'matplotlib',
        'seaborn',
        'cryptography',
        'redis',
        'pyyaml',
        'yaml',
        'toml',
        'requests',
        'jinja2',
        'websockets',
        'speech_recognition',
        'pyttsx3',
        'pyaudio',
        'json',
        'sqlite3',
        'threading',
        'multiprocessing',
        'queue',
        'collections',
        'dataclasses',
        'enum',
        'pathlib',
        'typing',
        'functools',
        'itertools',
        'contextlib',
        'concurrent.futures',
        'logging',
        'datetime',
        'time',
        'os',
        'sys',
        'subprocess',
        'platform',
        'shutil',
        'tempfile',
        'urllib',
        'zipfile',
        'tarfile',
        'hashlib',
        'base64',
        'secrets',
        'ssl',
        'socket',
        'http',
        'email',
        'mimetypes',
        'xml',
        'html',
        'csv',
        'configparser',
        'argparse',
        'getpass',
        'glob',
        'fnmatch',
        'linecache',
        'traceback',
        'warnings',
        'weakref',
        'gc',
        'ctypes',
        'struct',
        'array',
        'copy',
        'pickle',
        'shelve',
        'dbm',
        'gzip',
        'bz2',
        'lzma',
        'zlib',
        'binascii',
        'codecs',
        'locale',
        'calendar',
        'decimal',
        'fractions',
        'random',
        'statistics',
        'math',
        'cmath',
        're',
        'string',
        'textwrap',
        'unicodedata',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib.backends._backend_tk',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI-System-Installer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    {f"icon='{icon_path}'," if icon_path else ""}
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI-System-Installer',
)
'''

    spec_file = Path("AI-System-Installer.spec")
    with open(spec_file, 'w') as f:
        f.write(spec_content)
        
    return str(spec_file)

def build_executable():
    """Build the executable using PyInstaller."""
    print("🔨 Building Windows executable...")
    
    try:
        # Create spec file
        spec_file = create_pyinstaller_spec()
        
        # Run PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            spec_file
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ Executable built successfully")
        
        # Check if the executable was created
        exe_path = Path("dist/AI-System-Installer/AI-System-Installer.exe")
        if exe_path.exists():
            print(f"📁 Executable created: {exe_path}")
            
            # Copy to a more accessible location
            final_exe = Path("AI-System-Installer.exe")
            shutil.copy2(exe_path, final_exe)
            print(f"📁 Executable copied to: {final_exe}")
            
            # Get file size
            size_mb = final_exe.stat().st_size / (1024 * 1024)
            print(f"📊 Executable size: {size_mb:.1f} MB")
            
            return str(final_exe)
        else:
            print("❌ Executable not found after build")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_installer_package():
    """Create a complete installer package."""
    print("📦 Creating installer package...")
    
    try:
        # Create installer directory
        installer_dir = Path("installer_package")
        if installer_dir.exists():
            shutil.rmtree(installer_dir)
        installer_dir.mkdir()
        
        # Copy executable
        exe_path = Path("AI-System-Installer.exe")
        if exe_path.exists():
            shutil.copy2(exe_path, installer_dir / "AI-System-Installer.exe")
        
        # Create README for installer
        readme_content = """# AI System Installer

## Quick Installation

1. Double-click `AI-System-Installer.exe`
2. Follow the installation prompts
3. The installer will:
   - Check system requirements
   - Create a virtual environment
   - Install all dependencies
   - Copy source files
   - Create desktop shortcuts
   - Set up the system

## System Requirements

- Windows 7/8/10/11 (64-bit)
- Python 3.8 or higher
- At least 2GB free disk space
- Internet connection for downloading dependencies

## Installation Directory

The system will be installed to:
- `C:\\Program Files\\AI-System\\` (default)

## After Installation

- Use the desktop shortcut "AI-System" to start
- Or run `AI-System.bat` from the installation directory
- Access the web dashboard at http://localhost:8080
- Use voice commands by saying "Hey System"

## Uninstallation

Run `uninstall.bat` from the installation directory.

## Support

For issues or questions, please visit:
https://github.com/ai-system/ai-system
"""
        
        with open(installer_dir / "README.txt", 'w') as f:
            f.write(readme_content)
            
        # Create version info
        version_info = {
            "version": "1.0.0",
            "build_date": str(Path().cwd()),
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        import json
        with open(installer_dir / "version.json", 'w') as f:
            json.dump(version_info, f, indent=2)
            
        # Create ZIP package
        zip_path = Path("AI-System-v1.0.0-Windows-Installer.zip")
        shutil.make_archive(str(zip_path.with_suffix('')), 'zip', installer_dir)
        
        print(f"✅ Installer package created: {zip_path}")
        
        # Calculate checksums
        import hashlib
        
        checksums = {}
        for file_path in [exe_path, zip_path]:
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    content = f.read()
                    sha256_hash = hashlib.sha256(content).hexdigest()
                    checksums[file_path.name] = sha256_hash
                    
        # Write checksums
        with open("checksums.txt", 'w') as f:
            for filename, checksum in checksums.items():
                f.write(f"{checksum}  {filename}\n")
                
        print("✅ Checksums created")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create installer package: {e}")
        return False

def main():
    """Main entry point."""
    print("=" * 60)
    print("🔧 AI System Executable Builder")
    print("=" * 60)
    print()
    
    # Install PyInstaller if needed
    if not install_pyinstaller():
        return False
        
    # Build executable
    exe_path = build_executable()
    if not exe_path:
        return False
        
    # Create installer package
    if not create_installer_package():
        return False
        
    print("\n" + "=" * 60)
    print("🎉 Windows executable created successfully!")
    print("=" * 60)
    print()
    print("📁 Files created:")
    print(f"   • AI-System-Installer.exe (standalone installer)")
    print(f"   • AI-System-v1.0.0-Windows-Installer.zip (distribution package)")
    print(f"   • checksums.txt (file verification)")
    print()
    print("🚀 To install:")
    print("   1. Run AI-System-Installer.exe")
    print("   2. Follow the installation wizard")
    print("   3. Use desktop shortcut to start the system")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            input("\nBuild failed. Press Enter to exit...")
            sys.exit(1)
        else:
            input("\nBuild completed successfully! Press Enter to exit...")
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)