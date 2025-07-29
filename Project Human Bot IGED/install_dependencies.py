#!/usr/bin/env python3
"""
IGED Dependency Installer
Installs all required dependencies for IGED
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} error: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def upgrade_pip():
    """Upgrade pip to latest version"""
    return run_command(
        f"{sys.executable} -m pip install --upgrade pip",
        "Upgrading pip"
    )

def install_core_dependencies():
    """Install core dependencies"""
    core_deps = [
        "cryptography>=3.4.8",
        "flask>=2.3.3",
        "flask-cors>=4.0.0",
        "requests>=2.31.0"
    ]
    
    for dep in core_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            return False
    return True

def install_voice_dependencies():
    """Install voice recognition dependencies"""
    voice_deps = [
        "SpeechRecognition>=3.10.0",
        "openai-whisper>=20231117",
        "PyAudio>=0.2.11"
    ]
    
    for dep in voice_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️ Voice dependency {dep} failed - voice features may not work")
    return True

def install_data_analysis_dependencies():
    """Install data analysis dependencies"""
    data_deps = [
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "matplotlib>=3.7.0",
        "seaborn>=0.12.0"
    ]
    
    for dep in data_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️ Data analysis dependency {dep} failed - data analysis features may not work")
    return True

def install_security_dependencies():
    """Install security and network dependencies"""
    security_deps = [
        "python-nmap>=0.7.1",
        "psutil>=5.9.0"
    ]
    
    for dep in security_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️ Security dependency {dep} failed - security features may not work")
    return True

def install_build_dependencies():
    """Install build and development dependencies"""
    build_deps = [
        "pyinstaller>=5.13.0",
        "setuptools>=68.0.0",
        "wheel>=0.41.0"
    ]
    
    for dep in build_deps:
        if not run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}"):
            print(f"⚠️ Build dependency {dep} failed - build features may not work")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        "config",
        "memory",
        "logs",
        "output",
        "output/data_analysis",
        "output/security",
        "output/network_intelligence",
        "output/remote_control"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created directory: {directory}")
    
    return True

def generate_encryption_key():
    """Generate encryption key if it doesn't exist"""
    key_path = Path("config/secret.key")
    if not key_path.exists():
        print("🔐 Generating encryption key...")
        try:
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
            print("✅ Encryption key generated")
            return True
        except Exception as e:
            print(f"❌ Failed to generate encryption key: {e}")
            return False
    else:
        print("✅ Encryption key already exists")
        return True

def main():
    """Main installation function"""
    print("🚀 IGED Dependency Installer")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Upgrade pip
    upgrade_pip()
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    
    if not install_core_dependencies():
        print("❌ Core dependencies installation failed")
        sys.exit(1)
    
    install_voice_dependencies()
    install_data_analysis_dependencies()
    install_security_dependencies()
    install_build_dependencies()
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Generate encryption key
    print("\n🔐 Setting up encryption...")
    generate_encryption_key()
    
    print("\n" + "=" * 40)
    print("✅ Installation completed!")
    print("\n🎯 Next steps:")
    print("1. Run: python test_installation.py")
    print("2. Launch IGED: python launcher.py")
    print("3. Access web admin: http://localhost:8080")
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main() 