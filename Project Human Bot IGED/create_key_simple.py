#!/usr/bin/env python3
"""
Simple Encryption Key Generator using subprocess
"""

import subprocess
import os
import base64

def create_key_with_subprocess():
    """Create encryption key using subprocess"""
    
    print("🔑 Creating encryption key using subprocess...")
    
    try:
        # Generate key using Python subprocess
        result = subprocess.run([
            'python', '-c', 
            'from cryptography.fernet import Fernet; import base64; key = Fernet.generate_key(); print(base64.b64encode(key).decode())'
        ], capture_output=True, text=True, check=True)
        
        # Get the key from output
        key_b64 = result.stdout.strip()
        key = base64.b64decode(key_b64)
        
        print(f"✅ Key generated: {len(key)} bytes")
        
        # Write key using subprocess
        subprocess.run([
            'python', '-c', 
            f'import base64; key = base64.b64decode("{key_b64}"); open("config/secret.key", "wb").write(key)'
        ], check=True)
        
        print("✅ Key saved to config/secret.key")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Subprocess error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_key_with_subprocess()
    if success:
        print("🎉 Encryption key created successfully!")
    else:
        print("❌ Failed to create encryption key")  
