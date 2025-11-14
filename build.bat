@echo off
REM ImageViewer Build Script for Windows (Batch)
REM Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

echo ImageViewer Build Script for Windows
echo ====================================
echo.
echo This batch file is a simple wrapper for the Python cross-platform build script.
echo For full functionality, consider using PowerShell or the Python wrapper directly.
echo.
echo Usage: build.bat [options]
echo.
echo Options:
echo   --type exe     Build executable only
echo   --type wheel   Build Python wheel only
echo   --type all     Build both (default)
echo   --clean        Clean build directories first
echo   --help         Show detailed help
echo.
echo Examples:
echo   build.bat
echo   build.bat --clean
echo   build.bat --type exe
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found in PATH
    echo Please ensure Python 3.8+ is installed and in your PATH
    pause
    exit /b 1
)

REM Run the Python cross-platform build script
python build.py %*

if %errorlevel% neq 0 (
    echo.
    echo Build failed with error code %errorlevel%
    pause
    exit /b %errorlevel%
)

echo.
echo Build completed successfully!
pause
