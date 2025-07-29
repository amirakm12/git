"""
Encryption Manager for IGED
Handles AES-256 encryption for sensitive data
"""

import os
import base64
import logging
from pathlib import Path
from typing import Optional, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class EncryptionManager:
    def __init__(self, key_path: str = "config/secret.key"):
        self.key_path = Path(key_path)
        self.key = None
        self.cipher = None
        self.initialize_encryption()
    
    def initialize_encryption(self):
        """Initialize encryption with key generation or loading"""
        try:
            # Create config directory if it doesn't exist
            self.key_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load or generate encryption key
            if self.key_path.exists():
                self.load_key()
            else:
                self.generate_key()
            
            # Initialize Fernet cipher
            self.cipher = Fernet(self.key)
            logger.info("✅ Encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize encryption: {e}")
            raise
    
    def generate_key(self):
        """Generate a new encryption key"""
        try:
            # Generate a new Fernet key
            self.key = Fernet.generate_key()
            
            # Save key to file
            with open(self.key_path, 'wb') as f:
                f.write(self.key)
            
            logger.info(f"🔑 Generated new encryption key: {self.key_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate encryption key: {e}")
            raise
    
    def load_key(self):
        """Load encryption key from file"""
        try:
            with open(self.key_path, 'rb') as f:
                self.key = f.read()
            
            logger.info(f"🔑 Loaded encryption key from: {self.key_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load encryption key: {e}")
            raise
    
    def encrypt(self, data: Union[str, bytes]) -> str:
        """Encrypt data using AES-256"""
        try:
            if not self.cipher:
                raise ValueError("Encryption not initialized")
            
            # Convert string to bytes if necessary
            if isinstance(data, str):
                data = data.encode('utf-8')
            
            # Encrypt using Fernet
            encrypted_data = self.cipher.encrypt(data)
            
            # Return base64 encoded string
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_data: Union[str, bytes]) -> str:
        """Decrypt data using AES-256"""
        try:
            if not self.cipher:
                raise ValueError("Encryption not initialized")
            
            # Convert string to bytes if necessary
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')
            
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Decrypt using Fernet
            decrypted_data = self.cipher.decrypt(encrypted_bytes)
            
            # Return as string
            return decrypted_data.decode('utf-8')
            
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Encrypt a file"""
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path_obj}")
            
            # Read file content
            with open(path_obj, 'rb') as f:
                file_data = f.read()
            
            # Encrypt data
            encrypted_data = self.encrypt(file_data)
            
            # Determine output path
            if output_path is None:
                output_path = str(path_obj) + '.encrypted'
            
            # Write encrypted data
            with open(output_path, 'w') as f:
                f.write(encrypted_data)
            
            logger.info(f"🔒 Encrypted file: {path_obj} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File encryption failed: {e}")
            raise
    
    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """Decrypt a file"""
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {path_obj}")
            
            # Read encrypted data
            with open(path_obj, 'r') as f:
                encrypted_data = f.read()
            
            # Decrypt data
            decrypted_data = self.decrypt(encrypted_data)
            
            # Determine output path
            if output_path is None:
                if path_obj.suffix == '.encrypted':
                    output_path = str(path_obj)[:-10]  # Remove .encrypted
                else:
                    output_path = str(path_obj) + '.decrypted'
            
            # Write decrypted data
            with open(output_path, 'w') as f:
                f.write(decrypted_data)
            
            logger.info(f"🔓 Decrypted file: {path_obj} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"❌ File decryption failed: {e}")
            raise
    
    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary"""
        try:
            import json
            json_data = json.dumps(data, ensure_ascii=False)
            return self.encrypt(json_data)
            
        except Exception as e:
            logger.error(f"❌ Dictionary encryption failed: {e}")
            raise
    
    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt a dictionary"""
        try:
            import json
            json_data = self.decrypt(encrypted_data)
            return json.loads(json_data)
            
        except Exception as e:
            logger.error(f"❌ Dictionary decryption failed: {e}")
            raise
    
    def generate_password_hash(self, password: str, salt: Optional[bytes] = None) -> tuple:
        """Generate password hash using PBKDF2"""
        try:
            if salt is None:
                salt = os.urandom(16)
            
            # Generate key using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            return key, salt
            
        except Exception as e:
            logger.error(f"❌ Password hash generation failed: {e}")
            raise
    
    def verify_password(self, password: str, key: bytes, salt: bytes) -> bool:
        """Verify password against stored hash"""
        try:
            # Generate hash for verification
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            verify_key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            return key == verify_key
            
        except Exception as e:
            logger.error(f"❌ Password verification failed: {e}")
            return False
    
    def secure_delete(self, file_path: str, passes: int = 3):
        """Securely delete a file by overwriting with random data"""
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return
            
            file_size = path_obj.stat().st_size
            
            # Overwrite file multiple times
            for _ in range(passes):
                with open(path_obj, 'wb') as f:
                    # Write random data
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Delete file
            path_obj.unlink()
            
            logger.info(f"🗑️ Securely deleted file: {path_obj}")
            
        except Exception as e:
            logger.error(f"❌ Secure delete failed: {e}")
            raise
    
    def get_key_info(self) -> dict:
        """Get information about the encryption key"""
        try:
            return {
                'key_path': str(self.key_path),
                'key_exists': self.key_path.exists(),
                'key_size': len(self.key) if self.key else 0,
                'cipher_initialized': self.cipher is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get key info: {e}")
            return {}
    
    def rotate_key(self, new_key_path: Optional[str] = None):
        """Rotate encryption key"""
        try:
            # Generate new key
            old_key = self.key
            old_cipher = self.cipher
            
            if new_key_path:
                self.key_path = Path(new_key_path)
            
            self.generate_key()
            self.cipher = Fernet(self.key)
            
            logger.info("🔄 Encryption key rotated successfully")
            
            # Return old key for re-encryption if needed
            return old_key, old_cipher
            
        except Exception as e:
            logger.error(f"❌ Key rotation failed: {e}")
            raise
    
    def test_encryption(self) -> bool:
        """Test encryption/decryption functionality"""
        try:
            test_data = "IGED encryption test data"
            
            # Encrypt
            encrypted = self.encrypt(test_data)
            
            # Decrypt
            decrypted = self.decrypt(encrypted)
            
            # Verify
            success = test_data == decrypted
            
            if success:
                logger.info("✅ Encryption test passed")
            else:
                logger.error("❌ Encryption test failed")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Encryption test failed: {e}")
            return False 