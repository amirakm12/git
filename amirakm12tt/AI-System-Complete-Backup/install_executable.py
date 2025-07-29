#!/usr/bin/env python3
"""
AI System Executable Installer
Simple one-click installation for the AI System
"""

import os
import sys
import subprocess
import platform
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path
import json

class ExecutableInstaller:
    """Simple executable installer for AI System."""
    
    def __init__(self):
        self.system = platform.system()
        self.install_dir = self.get_install_directory()
        self.python_exe = sys.executable
        
    def choose_install_directory(self):
        """Allow user to choose custom installation directory."""
        default_dir = self.get_install_directory()
        print(f"\n📁 Installation Directory Selection")
        print(f"Default: {default_dir}")
        print("Press Enter to use default, or type a custom path:")
        
        custom_path = input("Custom path: ").strip()
        if custom_path:
            self.install_dir = Path(custom_path) / "AI-System"
            print(f"Using custom directory: {self.install_dir}")
        else:
            print(f"Using default directory: {self.install_dir}")
        
    def get_install_directory(self):
        """Get the appropriate installation directory."""
        if self.system == "Windows":
            # Use user's AppData directory instead of Program Files to avoid permission issues
            appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            return Path(appdata) / "AI-System"
        elif self.system == "Darwin":  # macOS
            return Path.home() / "Applications" / "AI-System"
        else:  # Linux and others
            return Path.home() / ".local" / "share" / "ai-system"
            
    def check_requirements(self):
        """Check system requirements."""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8 or higher is required")
            print(f"   Current version: {sys.version}")
            return False
            
        # Check pip
        try:
            subprocess.run([self.python_exe, "-m", "pip", "--version"], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ pip is not available")
            return False
            
        # Check write permissions for installation directory
        try:
            parent_dir = self.install_dir.parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write permission by creating a temporary file
            test_file = parent_dir / "test_write_permission.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
        except (PermissionError, OSError) as e:
            print(f"❌ Cannot write to installation directory: {parent_dir}")
            print(f"   Error: {e}")
            print("   Try running as administrator or choose a different location")
            return False
            
        print("✅ System requirements met")
        return True
        
    def create_virtual_environment(self):
        """Create a virtual environment for the installation."""
        print("📦 Creating virtual environment...")
        
        venv_dir = self.install_dir / "venv"
        
        try:
            subprocess.run([self.python_exe, "-m", "venv", str(venv_dir)], 
                         check=True, capture_output=True)
                         
            # Get the python executable in the virtual environment
            if self.system == "Windows":
                self.venv_python = venv_dir / "Scripts" / "python.exe"
                self.venv_pip = venv_dir / "Scripts" / "pip.exe"
            else:
                self.venv_python = venv_dir / "bin" / "python"
                self.venv_pip = venv_dir / "bin" / "pip"
                
            print("✅ Virtual environment created")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
            
    def install_dependencies(self):
        """Install required dependencies."""
        print("📥 Installing dependencies...")
        
        # Core dependencies
        dependencies = [
            "asyncio-mqtt>=0.16.1",
            "aiohttp>=3.9.1",
            "uvloop>=0.19.0",
            "psutil>=5.9.6",
            "GPUtil>=1.4.0",
            "torch>=2.1.2",
            "transformers>=4.36.2",
            "sentence-transformers>=2.2.2",
            "chromadb>=0.4.18",
            "langchain>=0.0.350",
            "openai>=1.6.1",
            "scikit-learn>=1.3.2",
            "numpy>=1.24.4",
            "pandas>=2.1.4",
            "matplotlib>=3.8.2",
            "seaborn>=0.13.0",
            "cryptography>=41.0.8",
            "redis>=5.0.1",
            "pyyaml>=6.0.1",
            "toml>=0.10.2",
            "requests>=2.31.0",
            "jinja2>=3.1.2",
            "websockets>=12.0",
        ]
        
        # Optional dependencies for voice interface
        voice_dependencies = [
            "SpeechRecognition>=3.10.0",
            "pyttsx3>=2.90",
            "pyaudio>=0.2.11",
        ]
        
        try:
            # Upgrade pip first
            subprocess.run([str(self.venv_pip), "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Install core dependencies
            for dep in dependencies:
                print(f"  Installing {dep}...")
                subprocess.run([str(self.venv_pip), "install", dep], 
                             check=True, capture_output=True)
                             
            # Try to install voice dependencies
            print("  Installing voice interface dependencies...")
            for dep in voice_dependencies:
                try:
                    subprocess.run([str(self.venv_pip), "install", dep], 
                                 check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    print(f"    ⚠️ Could not install {dep} (voice features may be limited)")
                    
            print("✅ Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
            
    def copy_source_files(self):
        """Copy source files to installation directory."""
        print("📁 Copying source files...")
        
        try:
            # Create directory structure
            src_dir = self.install_dir / "src"
            config_dir = self.install_dir / "config"
            data_dir = self.install_dir / "data"
            logs_dir = self.install_dir / "logs"
            
            for directory in [src_dir, config_dir, data_dir, logs_dir]:
                directory.mkdir(parents=True, exist_ok=True)
                
            # Copy source files from current directory
            current_dir = Path(__file__).parent
            
            if (current_dir / "src").exists():
                shutil.copytree(current_dir / "src", src_dir, dirs_exist_ok=True)
            if (current_dir / "config").exists():
                shutil.copytree(current_dir / "config", config_dir, dirs_exist_ok=True)
            if (current_dir / "requirements").exists():
                shutil.copytree(current_dir / "requirements", 
                              self.install_dir / "requirements", dirs_exist_ok=True)
                              
            # Copy important files
            for filename in ["README.md", "LICENSE", "setup.py"]:
                src_file = current_dir / filename
                if src_file.exists():
                    shutil.copy2(src_file, self.install_dir / filename)
                    
            print("✅ Source files copied")
            return True
            
        except Exception as e:
            print(f"❌ Failed to copy source files: {e}")
            return False
            
    def create_launcher_scripts(self):
        """Create launcher scripts."""
        print("🚀 Creating launcher scripts...")
        
        try:
            # Windows batch file
            if self.system == "Windows":
                launcher_content = f'''@echo off
cd /d "{self.install_dir}"
"{self.venv_python}" -m src.main %*
pause
'''
                launcher_path = self.install_dir / "AI-System.bat"
                with open(launcher_path, 'w') as f:
                    f.write(launcher_content)
                    
                # Create desktop shortcut
                desktop = Path.home() / "Desktop"
                if desktop.exists():
                    shortcut_content = f'''@echo off
cd /d "{self.install_dir}"
"{self.venv_python}" -m src.main
'''
                    shortcut_path = desktop / "AI-System.bat"
                    with open(shortcut_path, 'w') as f:
                        f.write(shortcut_content)
                        
            else:
                # Unix shell script
                launcher_content = f'''#!/bin/bash
cd "{self.install_dir}"
"{self.venv_python}" -m src.main "$@"
'''
                launcher_path = self.install_dir / "ai-system"
                with open(launcher_path, 'w') as f:
                    f.write(launcher_content)
                os.chmod(launcher_path, 0o755)
                
                # Create desktop entry for Linux
                if self.system == "Linux":
                    desktop_dir = Path.home() / ".local" / "share" / "applications"
                    desktop_dir.mkdir(parents=True, exist_ok=True)
                    
                    desktop_entry = f'''[Desktop Entry]
Name=AI System
Comment=Comprehensive Multi-Agent AI System
Exec={launcher_path}
Icon={self.install_dir}/assets/icon.png
Terminal=true
Type=Application
Categories=Development;Science;
'''
                    desktop_file = desktop_dir / "ai-system.desktop"
                    with open(desktop_file, 'w') as f:
                        f.write(desktop_entry)
                    os.chmod(desktop_file, 0o755)
                    
            print("✅ Launcher scripts created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create launcher scripts: {e}")
            return False
            
    def create_uninstaller(self):
        """Create uninstaller script."""
        print("🗑️ Creating uninstaller...")
        
        try:
            if self.system == "Windows":
                uninstall_content = f'''@echo off
echo Uninstalling AI System...
rmdir /s /q "{self.install_dir}"
del "%USERPROFILE%\\Desktop\\AI-System.bat"
echo AI System has been uninstalled.
pause
'''
                uninstall_path = self.install_dir / "uninstall.bat"
            else:
                uninstall_content = f'''#!/bin/bash
echo "Uninstalling AI System..."
rm -rf "{self.install_dir}"
rm -f "$HOME/.local/share/applications/ai-system.desktop"
echo "AI System has been uninstalled."
read -p "Press Enter to continue..."
'''
                uninstall_path = self.install_dir / "uninstall.sh"
                
            with open(uninstall_path, 'w') as f:
                f.write(uninstall_content)
                
            if self.system != "Windows":
                os.chmod(uninstall_path, 0o755)
                
            print("✅ Uninstaller created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create uninstaller: {e}")
            return False
            
    def create_config_files(self):
        """Create default configuration files."""
        print("⚙️ Creating configuration files...")
        
        try:
            config_dir = self.install_dir / "config"
            
            # Default system configuration
            default_config = {
                "ai_models": {
                    "model_name": "gpt-4",
                    "max_tokens": 4096,
                    "temperature": 0.7
                },
                "rag": {
                    "vector_db_path": "data/vector_db",
                    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                    "chunk_size": 1000
                },
                "kernel": {
                    "enable_monitoring": True,
                    "monitoring_interval": 60
                },
                "sensors": {
                    "fusion_algorithm": "kalman_filter",
                    "sampling_rate": 1.0
                },
                "ui": {
                    "dashboard_port": 8080,
                    "enable_voice": True
                }
            }
            
            config_file = config_dir / "config.json"
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            print("✅ Configuration files created")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create configuration files: {e}")
            return False
            
    def run_installation_test(self):
        """Run a quick installation test."""
        print("🧪 Running installation test...")
        
        try:
            # Test if the main module can be imported
            test_script = f'''
import sys
import os
sys.path.insert(0, "{self.install_dir}")
os.chdir("{self.install_dir}")
try:
    from src.main import AISystem
    print("✅ Installation test passed")
except ImportError as e:
    print(f"❌ Installation test failed: {{e}}")
    sys.exit(1)
'''
            
            result = subprocess.run([str(self.venv_python), "-c", test_script], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Installation test passed")
                return True
            else:
                print(f"❌ Installation test failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Installation test error: {e}")
            return False
            
    def install(self):
        """Main installation process."""
        print("=" * 60)
        print("🤖 AI System Executable Installer")
        print("=" * 60)
        print()
        
        # Let user choose installation directory
        self.choose_install_directory()
        
        # Check if already installed
        if self.install_dir.exists():
            response = input(f"AI System is already installed at {self.install_dir}.\n"
                           "Do you want to reinstall? (y/N): ")
            if response.lower() != 'y':
                print("Installation cancelled.")
                return False
            try:
                shutil.rmtree(self.install_dir)
            except PermissionError as e:
                print(f"❌ Cannot remove existing installation: {e}")
                print("Please remove the directory manually or run as administrator")
                return False
            
        # Create installation directory
        try:
            self.install_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            print(f"❌ Cannot create installation directory: {e}")
            print("Please choose a different location or run as administrator")
            return False
        
        # Run installation steps
        steps = [
            ("Checking requirements", self.check_requirements),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Copying source files", self.copy_source_files),
            ("Creating launcher scripts", self.create_launcher_scripts),
            ("Creating uninstaller", self.create_uninstaller),
            ("Creating configuration files", self.create_config_files),
            ("Running installation test", self.run_installation_test),
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"\n❌ Installation failed at step: {step_name}")
                return False
                
        print("\n" + "=" * 60)
        print("🎉 AI System installed successfully!")
        print("=" * 60)
        print(f"📁 Installation directory: {self.install_dir}")
        
        if self.system == "Windows":
            print("🚀 Run AI-System.bat to start the system")
            print("🖥️ Desktop shortcut created")
        else:
            print(f"🚀 Run {self.install_dir}/ai-system to start the system")
            if self.system == "Linux":
                print("🖥️ Desktop entry created")
                
        print(f"🗑️ To uninstall, run the uninstaller in {self.install_dir}")
        print()
        
        return True

def main():
    """Main entry point."""
    installer = ExecutableInstaller()
    
    try:
        success = installer.install()
        if success:
            input("\nPress Enter to exit...")
        else:
            input("\nInstallation failed. Press Enter to exit...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()