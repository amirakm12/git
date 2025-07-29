@echo off
chcp 65001 >nul
title AI System - Advanced Multi-Agent AI Platform

echo.
echo 🎯 AI System - Advanced Multi-Agent AI Platform
echo ================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

:: Check if we're in the right directory
if not exist "src\main.py" (
    echo ❌ Could not find src\main.py
    echo Please run this script from the AI System directory
    pause
    exit /b 1
)

echo ✅ Found main.py
echo 🚀 Starting AI System...
echo.

:: Try to install dependencies if needed
echo 🔧 Checking dependencies...
python -c "import torch, transformers, sentence_transformers, openai, langchain" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
)

:: Run the AI system
echo 🚀 Launching AI System...
echo ================================================
python run_ai_system.py

if errorlevel 1 (
    echo.
    echo ❌ AI System encountered an error
    echo Check the logs above for details
    pause
) else (
    echo.
    echo ✅ AI System completed successfully
    pause
)