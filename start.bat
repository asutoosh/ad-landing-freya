@echo off
echo ================================
echo Starting Telegram Ad Bot
echo ================================
echo.

REM Check if venv exists
if not exist venv (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

echo Starting bot and worker in separate windows...
echo.
echo Bot window: Handles /start, /stop, /send commands
echo Worker window: Sends scheduled messages
echo.
echo Close this window to see both processes
echo Press Ctrl+C in each window to stop
echo.

REM Start bot in new window
start "Telegram Bot" cmd /k "venv\Scripts\activate.bat && python bot.py"

REM Wait a moment
timeout /t 2 >nul

REM Start worker in new window
start "Telegram Worker" cmd /k "venv\Scripts\activate.bat && python worker.py"

echo Both processes started!
echo Check the new windows for logs.
echo.
pause
