// SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
// SPDX-License-Identifier: GPL-3.0-only

/**
 * Cloudflare Worker to serve the installer script
 * Usage:
 *   Linux/macOS: curl https://advance-image-viewer.gossorg.in | bash
 *   Windows:    irm https://advance-image-viewer.gossorg.in | iex
 */

const REPO = "IntegerAlex/advance-image-viewer";
const BINARY_NAME = "imageviewer";
const INSTALL_DIR = "$HOME/.local/bin";
const WINDOWS_BINARY_NAME = "imageviewer.exe";
const WINDOWS_INSTALL_DIR = "$env:LOCALAPPDATA\\Programs\\advance-image-viewer";

const INSTALLER_SCRIPT_LINUX = `#!/bin/bash
# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

set -e

BINARY_NAME="` + BINARY_NAME + `"
INSTALL_DIR="` + INSTALL_DIR + `"
RELEASE_URL="https://github.com/` + REPO + `/releases/latest"

echo "Installing advance-image-viewer..."
echo "Repository: ` + REPO + `"
echo "Install directory: ` + INSTALL_DIR + `"

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    x86_64)
        ARCH="x86_64"
        ;;
    aarch64|arm64)
        ARCH="aarch64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

echo "Detected: \${OS} \${ARCH}"

# Get latest release tag
echo "Fetching latest release..."
LATEST_TAG=$(curl -s "https://api.github.com/repos/` + REPO + `/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\\1/')

if [ -z "$LATEST_TAG" ]; then
    echo "Error: Could not fetch latest release tag"
    exit 1
fi

echo "Latest release: \${LATEST_TAG}"

# Construct download URL
# Assuming release assets are named like: imageviewer-linux-x86_64, imageviewer-linux-aarch64
ASSET_NAME="imageviewer-\${OS}-\${ARCH}"
DOWNLOAD_URL="https://github.com/` + REPO + `/releases/download/\${LATEST_TAG}/\${ASSET_NAME}"

echo "Downloading from: \${DOWNLOAD_URL}"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Download binary
TEMP_FILE=$(mktemp)
if curl -L -f -o "$TEMP_FILE" "$DOWNLOAD_URL"; then
    echo "Download successful"
else
    echo "Error: Failed to download binary"
    echo "Tried URL: \${DOWNLOAD_URL}"
    echo "Available releases: https://github.com/` + REPO + `/releases"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Make binary executable
chmod +x "$TEMP_FILE"

# Install to target directory
INSTALL_PATH="\${INSTALL_DIR}/\${BINARY_NAME}"
mv "$TEMP_FILE" "$INSTALL_PATH"

echo "Installed to: \${INSTALL_PATH}"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":\${INSTALL_DIR}:"* ]]; then
    echo ""
    echo "Warning: \${INSTALL_DIR} is not in your PATH"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\\\\$HOME/.local/bin:\\$PATH"
    echo ""
    echo "Then run: source ~/.bashrc  (or source ~/.zshrc)"
fi

echo ""
echo "Installation complete!"
echo "Run: \${BINARY_NAME} <image_path>"
echo "Or: \${INSTALL_PATH} <image_path>"
`;

const INSTALLER_SCRIPT_WINDOWS = `# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

$ErrorActionPreference = "Stop"

$BINARY_NAME = "` + WINDOWS_BINARY_NAME + `"
$INSTALL_DIR = "` + WINDOWS_INSTALL_DIR + `"
$RELEASE_URL = "https://github.com/` + REPO + `/releases/latest"

Write-Host "Installing advance-image-viewer..." -ForegroundColor Cyan
Write-Host "Repository: ` + REPO + `"
Write-Host "Install directory: ` + WINDOWS_INSTALL_DIR + `"

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
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/` + REPO + `/releases/latest"
    $LATEST_TAG = $response.tag_name
} catch {
    Write-Host "Error: Could not fetch latest release tag" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host "Latest release: $LATEST_TAG"

# Construct download URL
$ASSET_NAME = "imageviewer-windows-$ARCH.exe"
$DOWNLOAD_URL = "https://github.com/` + REPO + `/releases/download/$LATEST_TAG/$ASSET_NAME"

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
    Write-Host "Available releases: https://github.com/` + REPO + `/releases"
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
`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle CORS for preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    // Only allow GET requests
    if (request.method !== 'GET') {
      return new Response('Method not allowed', { status: 405 });
    }

    // Detect Windows via User-Agent or path
    const userAgent = request.headers.get('User-Agent') || '';
    const isWindows = userAgent.includes('Windows') || 
                      userAgent.includes('Win64') || 
                      userAgent.includes('Win32') ||
                      url.pathname === '/install.ps1' ||
                      url.pathname === '/install-windows.ps1';

    // Serve Windows PowerShell installer
    if (isWindows && (url.pathname === '/' || url.pathname === '/install.ps1' || url.pathname === '/install-windows.ps1')) {
      return new Response(INSTALLER_SCRIPT_WINDOWS, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Content-Disposition': 'inline; filename="install.ps1"',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        },
      });
    }

    // Serve Linux/macOS bash installer
    if (url.pathname === '/' || url.pathname === '/install.sh' || url.pathname === '/install') {
      return new Response(INSTALLER_SCRIPT_LINUX, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Content-Disposition': 'inline; filename="install.sh"',
          'Access-Control-Allow-Origin': '*',
          'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        },
      });
    }

    // Health check endpoint
    if (url.pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok', service: 'advance-image-viewer-installer' }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }

    // 404 for other paths
    return new Response('Not found', { status: 404 });
  },
};

