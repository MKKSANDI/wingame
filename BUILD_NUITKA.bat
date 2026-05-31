@echo off
setlocal enabledelayedexpansion
title WinGame Nuitka Build

echo ============================================
echo   WinGame - Nuitka Standalone Builder
echo ============================================
echo/

REM --- CONFIGURE BUILD TOOLS PATH HERE ---
set "VS_DEV_CMD=D:\Visual build tools\VC\Auxiliary\Build\vcvarsall.bat"

if not exist "%VS_DEV_CMD%" (
    echo [ERROR] Could not find vcvarsall.bat at:
    echo         %VS_DEV_CMD%
    echo Please update VS_DEV_CMD in BUILD_NUITKA.bat.
    goto :end
)

echo [1/4] Initializing MSVC environment...
call "%VS_DEV_CMD%" x64
if errorlevel 1 (
    echo [ERROR] Failed to initialize Visual Studio build tools.
    goto :end
)

echo [2/4] Ensuring Python dependencies...
python --version >nul 2>&1 || (
    echo [ERROR] Python is not available in PATH.
    goto :end
)

pip install --upgrade pip >nul
pip install -r requirements.txt >nul
pip install --upgrade nuitka ordered-set zstandard dill >nul

echo [3/4] Cleaning previous Nuitka artifacts...
if exist build\ rmdir /s /q build
if exist dist_nuitka\ rmdir /s /q dist_nuitka

echo [4/4] Building WinGame.exe with Nuitka...
python -m nuitka ^
    --onefile ^
    --standalone ^
    --enable-plugin=pyqt6 ^
    --windows-disable-console ^
    --windows-icon-from-ico=WinGame.ico ^
    --include-data-file=WinGame.png=WinGame.png ^
    --include-data-file=system.png=system.png ^
    --include-data-file=game.png=game.png ^
    --output-dir=dist_nuitka ^
    --product-name="WinGame" ^
    --file-description="WinGame Performance Optimizer" ^
    --company-name="WinGame" ^
    --product-version=1.1.0 ^
    GamePerformanceOptimizer.py

if errorlevel 1 (
    echo.
    echo [ERROR] Nuitka build failed. Check the log above.
    goto :end
)

echo.
echo ============================================
echo Build complete!
echo Output: dist_nuitka\GamePerformanceOptimizer.exe
echo ============================================

:end
echo.
pause


