#!/usr/bin/env python3
"""
Temporary Key Generator - Creates key in memory and outputs as string
"""

import base64
from cryptography.fernet import Fernet

def generate_key_string():
    """Generate encryption key and return as base64 string"""
    try:
        # Generate key
        key = Fernet.generate_key()
        
        # Convert to base64 string
        key_string = base64.b64encode(key).decode('utf-8')
        
        print("🔑 Encryption Key Generated Successfully!")
        print("=" * 50)
        print(f"Key (base64): {key_string}")
        print("=" * 50)
        print("\n📋 Instructions:")
        print("1. Copy the key above")
        print("2. Create a file named 'config/secret.key'")
        print("3. Paste the key content into that file")
        print("4. Save the file")
        print("\n💡 Alternative: Run IGED and it will generate the key automatically")
        
        return key_string
        
    except Exception as e:
        print(f"❌ Error generating key: {e}")
        return None

if __name__ == "__main__":
    generate_key_string()  
