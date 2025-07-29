@echo off
echo ========================================
echo IGED - Project Human Bot Installer
echo ========================================

echo.
echo Installing IGED dependencies...

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo.
echo Installing Python dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

REM Create necessary directories
echo.
echo Creating directories...
if not exist "config" mkdir config
if not exist "memory" mkdir memory
if not exist "output" mkdir output
if not exist "logs" mkdir logs
if not exist "plugins" mkdir plugins

REM Generate encryption key if not exists
if not exist "config\secret.key" (
    echo.
    echo Generating encryption key...
    python -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); open('config/secret.key', 'wb').write(key)"
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To start IGED, run: python launcher.py
echo.
echo To build executable, run: build_installer.bat
echo.
pause 