@echo off
echo ============================================
echo AI System Installer Builder for Windows
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found, building installer...
echo.

REM Run the installer builder
python create_exe.py

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed successfully!
echo ============================================
echo.
echo Files created:
echo   - AI-System-Installer.exe
echo   - AI-System-v1.0.0-Windows-Installer.zip
echo   - checksums.txt
echo.
echo To distribute:
echo   1. Share AI-System-Installer.exe for direct installation
echo   2. Share the ZIP file for complete package
echo.
echo To install:
echo   Double-click AI-System-Installer.exe
echo.
pause