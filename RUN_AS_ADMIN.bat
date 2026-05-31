@echo off
:: Game Performance Optimizer - Admin Launcher
:: This script will run the optimizer with administrator privileges

echo ========================================
echo   Game Performance Optimizer
echo ========================================
echo.
echo Starting with administrator privileges...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    echo.
    pause
    exit /b 1
)

:: Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required dependencies...
    echo.
    pip install -r requirements.txt
    echo.
)

:: Run with admin privileges
powershell -Command "Start-Process python -ArgumentList 'GamePerformanceOptimizer.py' -Verb RunAs"

echo.
echo Application launched!
echo If the app doesn't open, make sure you clicked "Yes" on the UAC prompt.
echo.
timeout /t 3


