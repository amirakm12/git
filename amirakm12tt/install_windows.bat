@echo off
setlocal enabledelayedexpansion

echo ============================================
echo AI System Windows Installer
echo ============================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    echo Press any key to open Python download page...
    pause >nul
    start https://www.python.org/downloads/
    exit /b 1
)

echo Python found, checking version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

REM Set installation directory to user's AppData
set INSTALL_DIR=%LOCALAPPDATA%\AI-System
echo Installation directory: %INSTALL_DIR%

REM Check if already installed
if exist "%INSTALL_DIR%" (
    echo.
    echo AI System is already installed at %INSTALL_DIR%
    set /p REINSTALL="Do you want to reinstall? (y/N): "
    if /i not "!REINSTALL!"=="y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo Removing existing installation...
    rmdir /s /q "%INSTALL_DIR%" 2>nul
)

echo.
echo Creating installation directory...
mkdir "%INSTALL_DIR%" 2>nul
if errorlevel 1 (
    echo Error: Cannot create installation directory
    echo Please check permissions or choose a different location
    pause
    exit /b 1
)

echo.
echo Creating virtual environment...
python -m venv "%INSTALL_DIR%\venv"
if errorlevel 1 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment
call "%INSTALL_DIR%\venv\Scripts\activate.bat"

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing core dependencies...
python -m pip install ^
    asyncio-mqtt ^
    aiohttp ^
    uvloop ^
    psutil ^
    torch ^
    transformers ^
    sentence-transformers ^
    chromadb ^
    langchain ^
    openai ^
    scikit-learn ^
    numpy ^
    pandas ^
    matplotlib ^
    cryptography ^
    pyyaml ^
    requests ^
    jinja2 ^
    websockets

if errorlevel 1 (
    echo Warning: Some packages may have failed to install
    echo The system may still work with reduced functionality
)

echo.
echo Installing optional voice dependencies...
python -m pip install SpeechRecognition pyttsx3 pyaudio
if errorlevel 1 (
    echo Note: Voice interface dependencies failed to install
    echo Voice features will not be available
)

echo.
echo Copying source files...
xcopy /E /I /H /Y "%~dp0src" "%INSTALL_DIR%\src\"
xcopy /E /I /H /Y "%~dp0config" "%INSTALL_DIR%\config\"
xcopy /E /I /H /Y "%~dp0requirements" "%INSTALL_DIR%\requirements\"

copy "%~dp0README.md" "%INSTALL_DIR%\" >nul 2>&1
copy "%~dp0LICENSE" "%INSTALL_DIR%\" >nul 2>&1

echo.
echo Creating launcher script...
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo call venv\Scripts\activate.bat
echo python -m src.main %%*
echo pause
) > "%INSTALL_DIR%\AI-System.bat"

echo.
echo Creating desktop shortcut...
set DESKTOP=%USERPROFILE%\Desktop
(
echo @echo off
echo cd /d "%INSTALL_DIR%"
echo call venv\Scripts\activate.bat
echo python -m src.main
echo pause
) > "%DESKTOP%\AI-System.bat"

echo.
echo Creating uninstaller...
(
echo @echo off
echo echo Uninstalling AI System...
echo rmdir /s /q "%INSTALL_DIR%"
echo del "%DESKTOP%\AI-System.bat" 2^>nul
echo echo AI System has been uninstalled.
echo pause
) > "%INSTALL_DIR%\uninstall.bat"

echo.
echo Creating default configuration...
mkdir "%INSTALL_DIR%\data" 2>nul
mkdir "%INSTALL_DIR%\logs" 2>nul

echo.
echo Testing installation...
cd /d "%INSTALL_DIR%"
python -c "import sys; sys.path.insert(0, '.'); from src.main import AISystem; print('Installation test passed')"
if errorlevel 1 (
    echo Warning: Installation test failed
    echo The system may not work correctly
)

echo.
echo ============================================
echo Installation completed successfully!
echo ============================================
echo.
echo Installation directory: %INSTALL_DIR%
echo.
echo To start AI System:
echo   - Use desktop shortcut "AI-System"
echo   - Or run: %INSTALL_DIR%\AI-System.bat
echo   - Or open command prompt and run: %INSTALL_DIR%\AI-System.bat
echo.
echo Web dashboard will be available at: http://localhost:8080
echo.
echo To uninstall: Run %INSTALL_DIR%\uninstall.bat
echo.
echo Press any key to exit...
pause >nul