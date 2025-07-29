@echo off
echo Generating IGED encryption key...

REM Create a Python script to generate the key
echo import base64 > temp_key_gen.py
echo from cryptography.fernet import Fernet >> temp_key_gen.py
echo key = Fernet.generate_key() >> temp_key_gen.py
echo with open('config/secret.key', 'wb') as f: >> temp_key_gen.py
echo     f.write(key) >> temp_key_gen.py
echo print('Key generated successfully') >> temp_key_gen.py

REM Run the script
python temp_key_gen.py

REM Clean up
del temp_key_gen.py

echo Key generation complete!
pause 