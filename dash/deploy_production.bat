@echo off
REM Production Deployment Script for Windows

echo === KSEB Dash Application - Production Deployment (Windows) ===
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt

echo.
echo === Starting Production Server ===
echo Using: Waitress (Windows production server)
echo Port: 8050
echo Access: http://localhost:8050
echo.

REM Run with waitress (Windows)
waitress-serve --host=0.0.0.0 --port=8050 --threads=8 app_optimized:server

REM Alternative: Use gunicorn with eventlet on Windows
REM pip install eventlet
REM gunicorn app_optimized:server --workers 4 --worker-class eventlet --bind 0.0.0.0:8050
