@echo off
echo ========================================
echo IGED - Project Human Bot Builder
echo ========================================

echo.
echo Building IGED executable...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Create build directory
if not exist "build_release" mkdir build_release

REM Build executable
echo.
echo Creating executable...
pyinstaller --noconfirm --onefile --windowed ^
    --add-data "config;config" ^
    --add-data "plugins;plugins" ^
    --add-data "agents;agents" ^
    --add-data "ui;ui" ^
    --add-data "admin_panel;admin_panel" ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    --hidden-import tkinter.scrolledtext ^
    --hidden-import tkinter.messagebox ^
    --hidden-import flask ^
    --hidden-import flask_cors ^
    --hidden-import speech_recognition ^
    --hidden-import whisper ^
    --hidden-import cryptography ^
    --hidden-import psutil ^
    --hidden-import pandas ^
    --hidden-import numpy ^
    --hidden-import matplotlib ^
    --hidden-import seaborn ^
    --hidden-import requests ^
    --hidden-import nmap ^
    --name "IGED" ^
    launcher.py

REM Copy additional files
echo.
echo Copying additional files...
copy "README.md" "build_release\"
copy "requirements.txt" "build_release\"
copy "offline_mode.py" "build_release\"
copy "watchdog.py" "build_release\"

REM Create directories
if not exist "build_release\output" mkdir build_release\output
if not exist "build_release\memory" mkdir build_release\memory
if not exist "build_release\logs" mkdir build_release\logs

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: build_release\IGED.exe
echo.
echo To create an installer, run: installer_script.nsi
echo.
pause 