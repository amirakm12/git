#!/usr/bin/env python3
"""
Generate encryption key for IGED
"""

import os
from pathlib import Path
from cryptography.fernet import Fernet

def generate_key():
    """Generate encryption key"""
    try:
        # Get current directory
        current_dir = Path.cwd()
        config_dir = current_dir / "config"
        key_file = config_dir / "secret.key"
        
        # Create config directory if it doesn't exist
        config_dir.mkdir(exist_ok=True)
        
        # Generate key
        key = Fernet.generate_key()
        
        # Save key
        with open(key_file, 'wb') as f:
            f.write(key)
        
        print("✅ Encryption key generated successfully")
        print(f"📁 Key saved to: {key_file}")
        print(f"🔑 Key length: {len(key)} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate key: {e}")
        return False

if __name__ == "__main__":
    generate_key() 