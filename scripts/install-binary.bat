@echo off
REM SPDX-License-Identifier: GPL-3.0-only
REM Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
REM
REM Installer script for imageviewer binary
REM This script installs the binary to a directory in PATH

setlocal enabledelayedexpansion

echo Installing imageviewer binary...

REM Get the directory where the script is located
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%\.."

set "BINARY_NAME=imageviewer.exe"
set "BINARY_PATH=dist\%BINARY_NAME%"

REM Check if binary exists
if not exist "%BINARY_PATH%" (
    echo Error: Binary not found at %BINARY_PATH%
    echo Please run scripts\build.bat first to build the binary.
    exit /b 1
)

REM Determine install location
set "INSTALL_DIR="
set "USE_ADMIN=false"

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% == 0 (
    set "INSTALL_DIR=C:\Program Files\imageviewer"
    set "USE_ADMIN=false"
) else (
    echo Choose installation type:
    echo   1) System-wide (requires admin) - installs to C:\Program Files\imageviewer
    echo   2) User-only - installs to %LOCALAPPDATA%\Programs\imageviewer
    set /p "choice=Enter choice [1-2] (default: 2): "
    if "!choice!"=="" set "choice=2"
    if "!choice!"=="1" (
        set "INSTALL_DIR=C:\Program Files\imageviewer"
        set "USE_ADMIN=true"
    ) else (
        set "INSTALL_DIR=%LOCALAPPDATA%\Programs\imageviewer"
        set "USE_ADMIN=false"
    )
)

REM Create install directory if it doesn't exist
echo Creating directory %INSTALL_DIR%...
if "%USE_ADMIN%"=="true" (
    REM Try to create directory with admin privileges
    mkdir "%INSTALL_DIR%" 2>nul
    if not exist "%INSTALL_DIR%" (
        echo Error: Failed to create directory. You may need to run as administrator.
        exit /b 1
    )
) else (
    mkdir "%INSTALL_DIR%" 2>nul
)

REM Check if binary already exists in install location
set "INSTALL_PATH=%INSTALL_DIR%\%BINARY_NAME%"
if exist "%INSTALL_PATH%" (
    echo Binary already exists at %INSTALL_PATH%
    set /p "overwrite=Overwrite? [y/N]: "
    if /i not "!overwrite!"=="y" (
        echo Installation cancelled.
        exit /b 0
    )
)

REM Copy binary to install location
echo Installing %BINARY_NAME% to %INSTALL_DIR%...
copy /Y "%BINARY_PATH%" "%INSTALL_PATH%" >nul
if errorlevel 1 (
    echo Error: Failed to copy binary.
    exit /b 1
)

REM Verify installation
if exist "%INSTALL_PATH%" (
    echo Installation successful!
    echo Binary installed to: %INSTALL_PATH%
    
    REM Check if install directory is in PATH
    echo %PATH% | findstr /C:"%INSTALL_DIR%" >nul
    if errorlevel 1 (
        echo Warning: %INSTALL_DIR% is not in your PATH
        echo Adding to PATH...
        
        REM Get current user PATH
        for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "CURRENT_PATH=%%B"
        
        REM Check if already in PATH
        echo !CURRENT_PATH! | findstr /C:"%INSTALL_DIR%" >nul
        if errorlevel 1 (
            REM Add to PATH
            if defined CURRENT_PATH (
                setx PATH "!CURRENT_PATH!;%INSTALL_DIR%" >nul
            ) else (
                setx PATH "%INSTALL_DIR%" >nul
            )
            echo Added %INSTALL_DIR% to PATH
            echo Please restart your terminal or command prompt for changes to take effect.
        ) else (
            echo %INSTALL_DIR% is already in PATH
        )
    ) else (
        echo %INSTALL_DIR% is already in PATH
    )
    
    REM Test the installation
    echo Testing installation...
    where %BINARY_NAME% >nul 2>&1
    if errorlevel 1 (
        echo Command not found in PATH. You may need to restart your terminal.
        echo You can run it directly from: %INSTALL_PATH%
    ) else (
        echo Command '%BINARY_NAME%' is available
        echo You can now run: imageviewer ^<image_path^>
    )
) else (
    echo Installation failed!
    exit /b 1
)

endlocal
