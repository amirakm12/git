import os
from cryptography.fernet import Fernet

# Create config directory if it doesn't exist
os.makedirs('config', exist_ok=True)

# Generate key
key = Fernet.generate_key()

# Save key
with open('config/secret.key', 'wb') as f:
    f.write(key)

print('✅ Encryption key generated successfully')
print(f'📁 Key saved to: config/secret.key')
print(f'🔑 Key length: {len(key)} bytes')  
