#!/usr/bin/env python3
"""
AI System Launcher
Direct launcher for the AI System without compilation
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_dependencies():
    """Install required dependencies"""
    print("🔧 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_ai_system():
    """Run the AI system"""
    print("🚀 Starting AI System...")
    print("=" * 50)
    
    try:
        # Add the current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        # Import and run the main system
        from src.main import run_system
        run_system()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Trying to install missing dependencies...")
        if install_dependencies():
            print("🔄 Retrying...")
            try:
                from src.main import run_system
                run_system()
            except Exception as e2:
                print(f"❌ Still failed: {e2}")
        else:
            print("❌ Could not install dependencies")
    except Exception as e:
        print(f"❌ Error running AI System: {e}")
        print("🔧 Troubleshooting:")
        print("  1. Make sure all files are present")
        print("  2. Check that Python is properly installed")
        print("  3. Try running: python -m pip install -r requirements.txt")

def main():
    """Main entry point"""
    print("🎯 AI System - Advanced Multi-Agent AI Platform")
    print("================================================")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {Path.cwd()}")
    print("")
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check if main.py exists
    main_file = Path("src/main.py")
    if not main_file.exists():
        print("❌ Could not find src/main.py")
        print("📁 Available files:")
        for item in Path.cwd().iterdir():
            print(f"  • {item.name}")
        return
    
    print("✅ Found main.py")
    
    # Try to run the system
    run_ai_system()

if __name__ == "__main__":
    main()