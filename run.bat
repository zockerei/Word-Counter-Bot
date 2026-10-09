@echo off
cd /d "%~dp0"

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install it first.
    pause
    exit /b
)

:: Create the virtual environment and install packages on first run
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment...
    python -m venv .venv
    .venv\Scripts\python.exe -m pip install --upgrade pip
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo Setup complete.
)

:: Start the bot with the venv's Python
.venv\Scripts\python.exe bot.py

:: Keep the command prompt open
pause
