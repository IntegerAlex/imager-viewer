#!/bin/bash
# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

set -e

REPO="IntegerAlex/advance-image-viewer"
BINARY_NAME="imageviewer"
INSTALL_DIR="$HOME/.local/bin"
RELEASE_URL="https://github.com/${REPO}/releases/latest"

echo "Installing advance-image-viewer..."
echo "Repository: ${REPO}"
echo "Install directory: ${INSTALL_DIR}"

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

echo "Detected: ${OS} ${ARCH}"

# Get latest release tag
echo "Fetching latest release..."
LATEST_TAG=$(curl -s "https://api.github.com/repos/${REPO}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')

if [ -z "$LATEST_TAG" ]; then
    echo "Error: Could not fetch latest release tag"
    exit 1
fi

echo "Latest release: ${LATEST_TAG}"

# Construct download URL
# Assuming release assets are named like: imageviewer-linux-x86_64, imageviewer-linux-aarch64
ASSET_NAME="imageviewer-${OS}-${ARCH}"
DOWNLOAD_URL="https://github.com/${REPO}/releases/download/${LATEST_TAG}/${ASSET_NAME}"

echo "Downloading from: ${DOWNLOAD_URL}"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Download binary
TEMP_FILE=$(mktemp)
if curl -L -f -o "$TEMP_FILE" "$DOWNLOAD_URL"; then
    echo "Download successful"
else
    echo "Error: Failed to download binary"
    echo "Tried URL: ${DOWNLOAD_URL}"
    echo "Available releases: https://github.com/${REPO}/releases"
    rm -f "$TEMP_FILE"
    exit 1
fi

# Make binary executable
chmod +x "$TEMP_FILE"

# Install to target directory
INSTALL_PATH="${INSTALL_DIR}/${BINARY_NAME}"
mv "$TEMP_FILE" "$INSTALL_PATH"

echo "Installed to: ${INSTALL_PATH}"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":${INSTALL_DIR}:"* ]]; then
    echo ""
    echo "Warning: ${INSTALL_DIR} is not in your PATH"
    echo "Add this line to your ~/.bashrc or ~/.zshrc:"
    echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then run: source ~/.bashrc  (or source ~/.zshrc)"
fi

echo ""
echo "Installation complete!"
echo "Run: ${BINARY_NAME} <image_path>"
echo "Or: ${INSTALL_PATH} <image_path>"

