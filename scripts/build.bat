@echo off
REM SPDX-License-Identifier: GPL-3.0-only
REM Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
REM
REM Build script for imageviewer using PyInstaller
REM This script builds a standalone binary for Windows

setlocal enabledelayedexpansion

echo Building imageviewer binary...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo Error: Failed to install PyInstaller
        exit /b 1
    )
)

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\.."

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build using the spec file if it exists, otherwise use command line
if exist imageviewer.spec (
    echo Using imageviewer.spec file...
    python -m PyInstaller imageviewer.spec --clean
) else (
    echo Building with PyInstaller...
    python -m PyInstaller ^
        --name=imageviewer ^
        --onefile ^
        --windowed ^
        --noconsole ^
        --hidden-import=PIL._tkinter_finder ^
        --add-data="src;src" ^
        main.py
)

REM Check if build was successful
if exist "dist\imageviewer.exe" (
    echo Build successful!
    echo Binary location: dist\imageviewer.exe
    dir dist
) else (
    echo Build failed!
    exit /b 1
)

endlocal
