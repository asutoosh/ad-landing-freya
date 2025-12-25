@echo off
echo ================================
echo Telegram Ad Bot - Setup Script
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

echo [1/5] Python found
python --version

REM Create virtual environment
echo.
echo [2/5] Creating virtual environment...
if not exist venv (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

REM Create directories
echo.
echo [4/5] Creating directories...
if not exist storage mkdir storage
if not exist media mkdir media
echo Directories created

REM Setup .env file
echo.
echo [5/5] Setting up .env file...
if not exist .env (
    copy .env.example .env
    echo.
    echo ================================
    echo IMPORTANT: Please edit .env file
    echo ================================
    echo.
    echo You need to configure:
    echo 1. TELEGRAM_BOT_TOKEN - Get from @BotFather
    echo 2. CHANNEL_URL - Your Telegram channel link
    echo 3. ADMIN_USER_ID - Your user ID from @userinfobot
    echo.
    echo Opening .env file for editing...
    timeout /t 2 >nul
    notepad .env
) else (
    echo .env file already exists
)

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo Next steps:
echo 1. Edit .env file if you haven't already
echo 2. Add media files to media/ folder (optional)
echo 3. Run the bot:
echo    - Terminal 1: venv\Scripts\python.exe bot.py
echo    - Terminal 2: venv\Scripts\python.exe worker.py
echo.
echo Or use: start.bat
echo.
pause
