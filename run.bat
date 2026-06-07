@echo off
title File System Assistant Launcher
cd /d "%~dp0"

echo ===================================================
echo   File System Assistant Launcher (Windows)
echo ===================================================

:: Check for Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

:: Create venv if missing
if not exist "venv\" (
    echo Creating virtual environment (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate venv and install/check dependencies
call venv\Scripts\activate
echo Checking / installing dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

:: Check for .env file
if not exist ".env" (
    echo [WARNING] Configuration file (.env) was not found!
    if exist ".env.example" (
        echo Copying .env.example to .env ...
        copy .env.example .env >nul
        echo [ACTION REQUIRED] Please open '.env' and paste your GROQ_API_KEY.
    ) else (
        echo [ERROR] Both .env and .env.example are missing.
    )
    pause
    exit /b 1
)

:: Check if GROQ_API_KEY is placeholder
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GROQ_API_KEY', '')
if not key or 'your_groq_api_key_here' in key:
    exit(1)
" >nul 2>&1

if %errorlevel% neq 0 (
    echo [ACTION REQUIRED] GROQ_API_KEY is empty or still has placeholder in '.env'.
    echo Please open '.env' and configure your Groq API Key first.
    pause
    exit /b 1
)

:: Launch the assistant
echo Launching Assistant...
python llm_file_assistant.py
pause
