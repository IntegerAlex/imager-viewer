# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

$ErrorActionPreference = "Stop"

$REPO = "IntegerAlex/advance-image-viewer"
$BINARY_NAME = "imageviewer.exe"
$INSTALL_DIR = "$env:LOCALAPPDATA\Programs\advance-image-viewer"
$RELEASE_URL = "https://github.com/$REPO/releases/latest"

Write-Host "Installing advance-image-viewer..." -ForegroundColor Cyan
Write-Host "Repository: $REPO"
Write-Host "Install directory: $INSTALL_DIR"

# Detect architecture
$ARCH = $env:PROCESSOR_ARCHITECTURE
if ($env:PROCESSOR_ARCHITEW6432) {
    $ARCH = $env:PROCESSOR_ARCHITEW6432
}

if ($ARCH -eq "AMD64") {
    $ARCH = "x86_64"
} elseif ($ARCH -eq "ARM64") {
    $ARCH = "aarch64"
} else {
    Write-Host "Unsupported architecture: $ARCH" -ForegroundColor Red
    exit 1
}

Write-Host "Detected: Windows $ARCH"

# Get latest release tag
Write-Host "Fetching latest release..."
try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$REPO/releases/latest"
    $LATEST_TAG = $response.tag_name
} catch {
    Write-Host "Error: Could not fetch latest release tag" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host "Latest release: $LATEST_TAG"

# Construct download URL
$ASSET_NAME = "imageviewer-windows-$ARCH.exe"
$DOWNLOAD_URL = "https://github.com/$REPO/releases/download/$LATEST_TAG/$ASSET_NAME"

Write-Host "Downloading from: $DOWNLOAD_URL"

# Create install directory if it doesn't exist
if (-not (Test-Path $INSTALL_DIR)) {
    New-Item -ItemType Directory -Path $INSTALL_DIR -Force | Out-Null
}

# Download binary
$TEMP_FILE = Join-Path $env:TEMP "imageviewer-installer.exe"
try {
    Invoke-WebRequest -Uri $DOWNLOAD_URL -OutFile $TEMP_FILE -ErrorAction Stop
    Write-Host "Download successful" -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to download binary" -ForegroundColor Red
    Write-Host "Tried URL: $DOWNLOAD_URL"
    Write-Host "Available releases: https://github.com/$REPO/releases"
    exit 1
}

# Install to target directory
$INSTALL_PATH = Join-Path $INSTALL_DIR $BINARY_NAME
Move-Item -Path $TEMP_FILE -Destination $INSTALL_PATH -Force

Write-Host "Installed to: $INSTALL_PATH" -ForegroundColor Green

# Check if install directory is in PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$INSTALL_DIR*") {
    Write-Host ""
    Write-Host "Warning: $INSTALL_DIR is not in your PATH" -ForegroundColor Yellow
    Write-Host "Adding to user PATH..."
    try {
        $newPath = $currentPath + ";$INSTALL_DIR"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        Write-Host "Added to PATH. Please restart your terminal for changes to take effect." -ForegroundColor Green
    } catch {
        Write-Host "Could not automatically add to PATH. Please add manually:" -ForegroundColor Yellow
        Write-Host "  $INSTALL_DIR"
    }
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "Run: $BINARY_NAME <image_path>"
Write-Host "Or: $INSTALL_PATH <image_path>"

