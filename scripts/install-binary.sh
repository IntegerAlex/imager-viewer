#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
#
# Installer script for imageviewer binary
# This script installs the binary to a directory in PATH

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

BINARY_NAME="imageviewer"
BINARY_PATH="dist/${BINARY_NAME}"

# Check if binary exists
if [ ! -f "$BINARY_PATH" ]; then
    echo -e "${RED}Error: Binary not found at $BINARY_PATH${NC}"
    echo -e "${YELLOW}Please run ./scripts/build.sh first to build the binary.${NC}"
    exit 1
fi

# Determine install location
INSTALL_DIR=""
USE_SUDO=false

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/bin"
    USE_SUDO=false
else
    # Try to use system-wide location (requires sudo)
    if command -v sudo &> /dev/null; then
        echo -e "${BLUE}Choose installation type:${NC}"
        echo -e "  1) System-wide (requires sudo) - installs to /usr/local/bin"
        echo -e "  2) User-only - installs to ~/.local/bin"
        read -p "Enter choice [1-2] (default: 2): " choice
        choice=${choice:-2}
        
        if [ "$choice" = "1" ]; then
            INSTALL_DIR="/usr/local/bin"
            USE_SUDO=true
        else
            INSTALL_DIR="$HOME/.local/bin"
            USE_SUDO=false
        fi
    else
        # No sudo available, use user directory
        INSTALL_DIR="$HOME/.local/bin"
        USE_SUDO=false
    fi
fi

# Create install directory if it doesn't exist
if [ "$USE_SUDO" = true ]; then
    echo -e "${YELLOW}Creating directory $INSTALL_DIR (requires sudo)...${NC}"
    sudo mkdir -p "$INSTALL_DIR"
else
    echo -e "${YELLOW}Creating directory $INSTALL_DIR...${NC}"
    mkdir -p "$INSTALL_DIR"
fi

# Check if binary already exists in install location
INSTALL_PATH="$INSTALL_DIR/$BINARY_NAME"
if [ -f "$INSTALL_PATH" ]; then
    echo -e "${YELLOW}Binary already exists at $INSTALL_PATH${NC}"
    read -p "Overwrite? [y/N]: " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Installation cancelled.${NC}"
        exit 0
    fi
fi

# Copy binary to install location
echo -e "${GREEN}Installing $BINARY_NAME to $INSTALL_DIR...${NC}"
if [ "$USE_SUDO" = true ]; then
    sudo cp "$BINARY_PATH" "$INSTALL_PATH"
    sudo chmod +x "$INSTALL_PATH"
else
    cp "$BINARY_PATH" "$INSTALL_PATH"
    chmod +x "$INSTALL_PATH"
fi

# Verify installation
if [ -f "$INSTALL_PATH" ] && [ -x "$INSTALL_PATH" ]; then
    echo -e "${GREEN}✓ Installation successful!${NC}"
    echo -e "${GREEN}Binary installed to: $INSTALL_PATH${NC}"
    
    # Check if install directory is in PATH
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo -e "${YELLOW}Warning: $INSTALL_DIR is not in your PATH${NC}"
        echo -e "${BLUE}To add it to your PATH, add this line to your ~/.bashrc or ~/.zshrc:${NC}"
        echo -e "${BLUE}export PATH=\"\$PATH:$INSTALL_DIR\"${NC}"
        
        # Offer to add it automatically
        read -p "Add to PATH automatically? [y/N]: " add_path
        if [[ "$add_path" =~ ^[Yy]$ ]]; then
            SHELL_RC=""
            if [ -f "$HOME/.bashrc" ]; then
                SHELL_RC="$HOME/.bashrc"
            elif [ -f "$HOME/.zshrc" ]; then
                SHELL_RC="$HOME/.zshrc"
            elif [ -f "$HOME/.profile" ]; then
                SHELL_RC="$HOME/.profile"
            fi
            
            if [ -n "$SHELL_RC" ]; then
                if ! grep -q "export PATH.*$INSTALL_DIR" "$SHELL_RC"; then
                    echo "" >> "$SHELL_RC"
                    echo "# Added by imageviewer installer" >> "$SHELL_RC"
                    echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
                    echo -e "${GREEN}✓ Added to $SHELL_RC${NC}"
                    echo -e "${YELLOW}Please run: source $SHELL_RC${NC}"
                    echo -e "${YELLOW}Or restart your terminal to use the command.${NC}"
                else
                    echo -e "${GREEN}PATH already configured in $SHELL_RC${NC}"
                fi
            else
                echo -e "${YELLOW}Could not find shell configuration file. Please add manually.${NC}"
            fi
        fi
    else
        echo -e "${GREEN}✓ $INSTALL_DIR is already in your PATH${NC}"
    fi
    
    # Test the installation
    echo -e "${BLUE}Testing installation...${NC}"
    if command -v "$BINARY_NAME" &> /dev/null; then
        INSTALLED_VERSION=$("$BINARY_NAME" --version 2>/dev/null || echo "installed")
        echo -e "${GREEN}✓ Command '$BINARY_NAME' is available${NC}"
        echo -e "${GREEN}You can now run: $BINARY_NAME <image_path>${NC}"
    else
        echo -e "${YELLOW}Command not found in PATH. You may need to restart your terminal.${NC}"
    fi
else
    echo -e "${RED}✗ Installation failed!${NC}"
    exit 1
fi
