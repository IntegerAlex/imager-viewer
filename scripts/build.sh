#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
#
# Build script for imageviewer using PyInstaller
# This script builds a standalone binary for Linux/Mac

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building imageviewer binary...${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed or not in PATH${NC}"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}PyInstaller not found. Installing...${NC}"
    python3 -m pip install pyinstaller
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Clean previous builds
echo -e "${YELLOW}Cleaning previous builds...${NC}"
rm -rf build dist

# Build using the spec file if it exists, otherwise use command line
if [ -f "imageviewer.spec" ]; then
    echo -e "${GREEN}Using imageviewer.spec file...${NC}"
    python3 -m PyInstaller imageviewer.spec --clean
else
    echo -e "${GREEN}Building with PyInstaller...${NC}"
    python3 -m PyInstaller \
        --name=imageviewer \
        --onefile \
        --windowed \
        --noconsole \
        --hidden-import=PIL._tkinter_finder \
        --add-data="src:src" \
        main.py
fi

# Check if build was successful
if [ -f "dist/imageviewer" ] || [ -f "dist/imageviewer.exe" ]; then
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo -e "${GREEN}Binary location: dist/imageviewer${NC}"
    ls -lh dist/
else
    echo -e "${RED}✗ Build failed!${NC}"
    exit 1
fi
