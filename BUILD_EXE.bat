@echo off
:: Build Game Performance Optimizer as standalone executable

echo ========================================
echo   Building Game Performance Optimizer
echo ========================================
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

:: Install PyInstaller if not already installed
echo Installing PyInstaller...
pip install pyinstaller
echo.

:: Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "GamePerformanceOptimizer.spec" del "GamePerformanceOptimizer.spec"

echo Building executable...
echo.

:: Build the executable
pyinstaller --onefile ^
    --windowed ^
    --name "GamePerformanceOptimizer" ^
    --add-data "README.md;." ^
    --add-data "QUICK_START.txt;." ^
    GamePerformanceOptimizer.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo ========================================
    echo.
    echo The executable is located in: dist\GamePerformanceOptimizer.exe
    echo.
    echo To run it:
    echo   1. Go to the 'dist' folder
    echo   2. Right-click GamePerformanceOptimizer.exe
    echo   3. Select "Run as administrator"
    echo.
    echo Copy these files to the dist folder:
    echo   - README.md
    echo   - QUICK_START.txt
    echo   - sample_config.json
    echo.
    
    :: Copy necessary files to dist
    copy README.md dist\ >nul 2>&1
    copy QUICK_START.txt dist\ >nul 2>&1
    copy sample_config.json dist\ >nul 2>&1
    
    echo Files copied to dist folder!
    echo.
) else (
    echo.
    echo ========================================
    echo   BUILD FAILED!
    echo ========================================
    echo.
    echo Please check the error messages above.
    echo.
)

pause


