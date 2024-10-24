@echo off

:: Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python is not installed. Please install it first.
    exit /b
)

:: Check if the virtual environment already exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv

    :: Activate the virtual environment
    call venv\Scripts\activate

    :: Upgrade pip
    python -m pip install --upgrade pip

    :: Install the required packages
    python -m pip install -r requirements.txt

    echo Setup complete. The virtual environment is now active.
) else (
    echo Virtual environment already exists. Activating...
    call venv\Scripts\activate
)

:: Start the bot
python bot.py

:: Keep the command prompt open
pause