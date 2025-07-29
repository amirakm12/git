import os
import sys
from pathlib import Path

print("=== Debug Key Generation ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python version: {sys.version}")

# Check config directory
config_path = Path("config")
print(f"Config path exists: {config_path.exists()}")
print(f"Config path is directory: {config_path.is_dir()}")
print(f"Config path is writable: {os.access(str(config_path), os.W_OK)}")

if config_path.exists():
    print(f"Config contents: {list(config_path.iterdir())}")

# Try to create the key file
try:
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    print(f"Key generated: {len(key)} bytes")
    
    # Try different path approaches
    key_path1 = config_path / "secret.key"
    key_path2 = Path("config/secret.key")
    key_path3 = Path("config\\secret.key")
    
    print(f"Key path 1: {key_path1}")
    print(f"Key path 2: {key_path2}")
    print(f"Key path 3: {key_path3}")
    
    # Try writing with pathlib
    key_path1.write_bytes(key)
    print("✅ Key saved successfully with pathlib!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc() 