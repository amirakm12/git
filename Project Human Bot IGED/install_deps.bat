@echo off
echo ========================================
echo IGED - Dependency Installer
echo ========================================

echo.
echo Checking Python installation...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install core dependencies
echo.
echo Installing core dependencies...
python -m pip install cryptography>=3.4.8
python -m pip install flask>=2.3.3
python -m pip install flask-cors>=4.0.0
python -m pip install requests>=2.31.0

REM Install voice dependencies
echo.
echo Installing voice recognition dependencies...
python -m pip install SpeechRecognition>=3.10.0
python -m pip install openai-whisper>=20231117
python -m pip install PyAudio>=0.2.11

REM Install data analysis dependencies
echo.
echo Installing data analysis dependencies...
python -m pip install pandas>=2.0.0
python -m pip install numpy>=1.24.0
python -m pip install matplotlib>=3.7.0
python -m pip install seaborn>=0.12.0

REM Install security dependencies
echo.
echo Installing security dependencies...
python -m pip install python-nmap>=0.7.1
python -m pip install psutil>=5.9.0

REM Install build dependencies
echo.
echo Installing build dependencies...
python -m pip install pyinstaller>=5.13.0
python -m pip install setuptools>=68.0.0
python -m pip install wheel>=0.41.0

REM Create directories FIRST
echo.
echo Creating directories...
if not exist "config" mkdir config
if not exist "memory" mkdir memory
if not exist "logs" mkdir logs
if not exist "output" mkdir output
if not exist "output\data_analysis" mkdir output\data_analysis
if not exist "output\security" mkdir output\security
if not exist "output\network_intelligence" mkdir output\network_intelligence
if not exist "output\remote_control" mkdir output\remote_control

REM Generate encryption key AFTER directories are created
echo.
echo Generating encryption key...
python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); open('config/secret.key', 'wb').write(key)"

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo.
echo Next steps:
echo 1. Run: python test_installation.py
echo 2. Launch IGED: python launcher.py
echo 3. Access web admin: http://localhost:8080
echo.
pause 