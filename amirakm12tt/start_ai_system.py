#!/usr/bin/env python3
"""
Simple AI System Launcher
Quick start without complex dependencies
"""

import sys
import asyncio
from pathlib import Path

def main():
    """Simple launcher that works"""
    print("🎯 AI System - Quick Start")
    print("=" * 30)
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path.cwd()))
        
        # Import and run the main system
        from src.main import run_system
        run_system()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("System files are saved locally and ready to use.")
        print("Run: python start_ai_system.py")

if __name__ == "__main__":
    main()