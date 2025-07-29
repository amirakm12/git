# AI System PowerShell Installer for Windows
# This installer does not require administrator privileges

param(
    [string]$InstallPath = "",
    [switch]$Force = $false
)

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AI System Windows Installer (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    
    # Check Python version
    $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
    if ($versionMatch) {
        $majorVersion = [int]$matches[1]
        $minorVersion = [int]$matches[2]
        if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
            Write-Host "❌ Python 3.8 or higher is required" -ForegroundColor Red
            Write-Host "Current version: $pythonVersion" -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://python.org" -ForegroundColor Yellow
    
    $openBrowser = Read-Host "Open Python download page? (y/N)"
    if ($openBrowser -eq "y" -or $openBrowser -eq "Y") {
        Start-Process "https://www.python.org/downloads/"
    }
    exit 1
}

# Set installation directory
if ($InstallPath -eq "") {
    $InstallPath = "$env:LOCALAPPDATA\AI-System"
}
Write-Host "📁 Installation directory: $InstallPath" -ForegroundColor Blue

# Check if already installed
if (Test-Path $InstallPath) {
    Write-Host
    Write-Host "⚠️  AI System is already installed at $InstallPath" -ForegroundColor Yellow
    
    if (-not $Force) {
        $reinstall = Read-Host "Do you want to reinstall? (y/N)"
        if ($reinstall -ne "y" -and $reinstall -ne "Y") {
            Write-Host "Installation cancelled." -ForegroundColor Yellow
            exit 0
        }
    }
    
    Write-Host "🗑️ Removing existing installation..." -ForegroundColor Yellow
    try {
        Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Host "❌ Cannot remove existing installation: $_" -ForegroundColor Red
        Write-Host "Please remove the directory manually: $InstallPath" -ForegroundColor Yellow
        exit 1
    }
}

# Create installation directory
Write-Host
Write-Host "📁 Creating installation directory..." -ForegroundColor Blue
try {
    New-Item -Path $InstallPath -ItemType Directory -Force -ErrorAction Stop | Out-Null
} catch {
    Write-Host "❌ Cannot create installation directory: $_" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "🐍 Creating virtual environment..." -ForegroundColor Blue
try {
    & python -m venv "$InstallPath\venv"
    if ($LASTEXITCODE -ne 0) {
        throw "Virtual environment creation failed"
    }
} catch {
    Write-Host "❌ Failed to create virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Activate virtual environment
$venvPython = "$InstallPath\venv\Scripts\python.exe"
$venvPip = "$InstallPath\venv\Scripts\pip.exe"

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Blue
& $venvPython -m pip install --upgrade pip --quiet

# Install core dependencies
Write-Host "📦 Installing core dependencies..." -ForegroundColor Blue
$coreDependencies = @(
    "asyncio-mqtt",
    "aiohttp",
    "psutil",
    "torch",
    "transformers",
    "sentence-transformers",
    "chromadb",
    "langchain",
    "openai",
    "scikit-learn",
    "numpy",
    "pandas",
    "matplotlib",
    "cryptography",
    "pyyaml",
    "requests",
    "jinja2",
    "websockets"
)

foreach ($package in $coreDependencies) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    try {
        & $venvPip install $package --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    ⚠️ Failed to install $package" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    ⚠️ Failed to install $package" -ForegroundColor Yellow
    }
}

# Install optional voice dependencies
Write-Host "🎤 Installing voice interface dependencies..." -ForegroundColor Blue
$voiceDependencies = @("SpeechRecognition", "pyttsx3", "pyaudio")

foreach ($package in $voiceDependencies) {
    Write-Host "  Installing $package..." -ForegroundColor Gray
    try {
        & $venvPip install $package --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    ⚠️ Failed to install $package (voice features may be limited)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "    ⚠️ Failed to install $package (voice features may be limited)" -ForegroundColor Yellow
    }
}

# Copy source files
Write-Host "📋 Copying source files..." -ForegroundColor Blue
$currentDir = Split-Path -Parent $MyInvocation.MyCommand.Path

try {
    # Copy main directories
    if (Test-Path "$currentDir\src") {
        Copy-Item -Path "$currentDir\src" -Destination "$InstallPath\src" -Recurse -Force
    }
    if (Test-Path "$currentDir\config") {
        Copy-Item -Path "$currentDir\config" -Destination "$InstallPath\config" -Recurse -Force
    }
    if (Test-Path "$currentDir\requirements") {
        Copy-Item -Path "$currentDir\requirements" -Destination "$InstallPath\requirements" -Recurse -Force
    }
    
    # Copy individual files
    $filesToCopy = @("README.md", "LICENSE", "setup.py")
    foreach ($file in $filesToCopy) {
        if (Test-Path "$currentDir\$file") {
            Copy-Item -Path "$currentDir\$file" -Destination "$InstallPath\$file" -Force
        }
    }
    
    # Create data and logs directories
    New-Item -Path "$InstallPath\data" -ItemType Directory -Force | Out-Null
    New-Item -Path "$InstallPath\logs" -ItemType Directory -Force | Out-Null
    
} catch {
    Write-Host "❌ Failed to copy source files: $_" -ForegroundColor Red
    exit 1
}

# Create launcher script
Write-Host "🚀 Creating launcher script..." -ForegroundColor Blue
$launcherContent = @"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python -m src.main %*
pause
"@
$launcherContent | Out-File -FilePath "$InstallPath\AI-System.bat" -Encoding ASCII

# Create desktop shortcut
Write-Host "🖥️ Creating desktop shortcut..." -ForegroundColor Blue
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutContent = @"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python -m src.main
pause
"@
$shortcutContent | Out-File -FilePath "$desktopPath\AI-System.bat" -Encoding ASCII

# Create uninstaller
Write-Host "🗑️ Creating uninstaller..." -ForegroundColor Blue
$uninstallerContent = @"
@echo off
echo Uninstalling AI System...
rmdir /s /q "$InstallPath"
del "$desktopPath\AI-System.bat" 2>nul
echo AI System has been uninstalled.
pause
"@
$uninstallerContent | Out-File -FilePath "$InstallPath\uninstall.bat" -Encoding ASCII

# Test installation
Write-Host "🧪 Testing installation..." -ForegroundColor Blue
try {
    Set-Location $InstallPath
    $testResult = & $venvPython -c "import sys; sys.path.insert(0, '.'); from src.main import AISystem; print('✅ Installation test passed')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $testResult -ForegroundColor Green
    } else {
        Write-Host "⚠️ Installation test failed: $testResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Installation test failed: $_" -ForegroundColor Yellow
}

# Installation complete
Write-Host
Write-Host "============================================" -ForegroundColor Green
Write-Host "🎉 Installation completed successfully!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host
Write-Host "📁 Installation directory: $InstallPath" -ForegroundColor Blue
Write-Host
Write-Host "🚀 To start AI System:" -ForegroundColor Blue
Write-Host "   • Use desktop shortcut 'AI-System'" -ForegroundColor Gray
Write-Host "   • Or run: $InstallPath\AI-System.bat" -ForegroundColor Gray
Write-Host "   • Or double-click the launcher in the installation directory" -ForegroundColor Gray
Write-Host
Write-Host "🌐 Web dashboard will be available at: http://localhost:8080" -ForegroundColor Blue
Write-Host "🎤 Voice interface: Say 'Hey System' to activate" -ForegroundColor Blue
Write-Host
Write-Host "🗑️ To uninstall: Run $InstallPath\uninstall.bat" -ForegroundColor Blue
Write-Host

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")