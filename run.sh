#!/bin/bash
cd "$(dirname "$0")"

echo "==================================================="
echo "  File System Assistant Launcher (Unix/macOS)"
echo "==================================================="

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed or not in PATH."
    exit 1
fi

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment (venv)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# Activate venv and check dependencies
source venv/bin/activate
echo "Checking / installing dependencies..."
python3 -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "[WARNING] Configuration file (.env) was not found!"
    if [ -f ".env.example" ]; then
        echo "Copying .env.example to .env ..."
        cp .env.example .env
        echo "[ACTION REQUIRED] Please open '.env' and paste your GROQ_API_KEY."
    else
        echo "[ERROR] Both .env and .env.example are missing."
    fi
    exit 1
fi

# Check if GROQ_API_KEY is placeholder
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GROQ_API_KEY', '')
if not key or 'your_groq_api_key_here' in key:
    exit(1)
" &> /dev/null

if [ $? -ne 0 ]; then
    echo "[ACTION REQUIRED] GROQ_API_KEY is empty or still has placeholder in '.env'."
    echo "Please open '.env' and configure your Groq API Key first."
    exit 1
fi

# Launch the assistant
echo "Launching Assistant..."
python3 llm_file_assistant.py
