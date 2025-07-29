#!/usr/bin/env python3
"""
Manual Encryption Key Generator for IGED
"""

import os
import sys
from pathlib import Path

def create_encryption_key():
    """Create encryption key with detailed error handling"""
    
    print("🔑 Creating IGED Encryption Key...")
    
    try:
        # Import cryptography
        from cryptography.fernet import Fernet
        print("✅ Cryptography imported successfully")
        
        # Generate key
        key = Fernet.generate_key()
        print(f"✅ Key generated: {len(key)} bytes")
        
        # Get current directory
        current_dir = Path.cwd()
        print(f"📁 Current directory: {current_dir}")
        
        # Create config path
        config_dir = current_dir / "config"
        print(f"📁 Config directory: {config_dir}")
        print(f"📁 Config exists: {config_dir.exists()}")
        print(f"📁 Config is directory: {config_dir.is_dir()}")
        
        # Create key file path
        key_file = config_dir / "secret.key"
        print(f"🔑 Key file path: {key_file}")
        
        # Try to write the key
        print("💾 Writing key to file...")
        key_file.write_bytes(key)
        
        # Verify the file was created
        if key_file.exists():
            print(f"✅ Key file created successfully!")
            print(f"📁 File size: {key_file.stat().st_size} bytes")
            print(f"🔑 Key file location: {key_file.absolute()}")
            return True
        else:
            print("❌ Key file was not created")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import cryptography: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating key: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_encryption_key()
    if success:
        print("\n🎉 Encryption key created successfully!")
        print("🚀 IGED is now ready to run!")
    else:
        print("\n❌ Failed to create encryption key")
        sys.exit(1) 