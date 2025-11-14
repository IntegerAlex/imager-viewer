#!/bin/bash
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
#
# Web installer script for ImageViewer
# Install with: curl -fsSL image-viewer.<domain>/install.sh | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REPO_OWNER="akshat"
REPO_NAME="imageviewer"
GITHUB_REPO="https://github.com/${REPO_OWNER}/${REPO_NAME}"
BINARY_NAME="imageviewer"
INSTALL_DIR="$HOME/.local/bin"

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS and architecture
detect_platform() {
    local os=$(uname -s | tr '[:upper:]' '[:lower:]')
    local arch=$(uname -m)
    
    case "$os" in
        linux*)
            OS="linux"
            ;;
        darwin*)
            OS="macos"
            ;;
        *)
            print_error "Unsupported OS: $os"
            exit 1
            ;;
    esac
    
    case "$arch" in
        x86_64|amd64)
            ARCH="x86_64"
            ;;
        aarch64|arm64)
            ARCH="arm64"
            ;;
        *)
            print_error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
    
    print_info "Detected platform: $OS $ARCH"
}

# Check for required commands
check_requirements() {
    local missing=()
    
    for cmd in curl tar; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -ne 0 ]; then
        print_error "Missing required commands: ${missing[*]}"
        print_info "Please install them using your package manager:"
        echo "  Ubuntu/Debian: sudo apt-get install curl tar"
        echo "  macOS: brew install curl"
        exit 1
    fi
}

# Get latest release version
get_latest_version() {
    print_info "Fetching latest release..."
    
    # Try to get latest release from GitHub
    if command -v jq &> /dev/null; then
        VERSION=$(curl -fsSL "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest" | jq -r .tag_name)
    else
        # Fallback without jq
        VERSION=$(curl -fsSL "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
    fi
    
    if [ -z "$VERSION" ] || [ "$VERSION" = "null" ]; then
        print_warning "No release found, will build from source"
        VERSION="main"
        BUILD_FROM_SOURCE=true
    else
        print_info "Latest version: $VERSION"
        BUILD_FROM_SOURCE=false
    fi
}

# Download and install binary
install_binary() {
    local download_url="${GITHUB_REPO}/releases/download/${VERSION}/${BINARY_NAME}-${OS}-${ARCH}"
    local temp_file="/tmp/${BINARY_NAME}"
    
    print_info "Downloading binary from $download_url"
    
    if curl -fsSL "$download_url" -o "$temp_file"; then
        chmod +x "$temp_file"
        
        # Create install directory
        mkdir -p "$INSTALL_DIR"
        
        # Install binary
        mv "$temp_file" "$INSTALL_DIR/$BINARY_NAME"
        print_success "Binary installed to $INSTALL_DIR/$BINARY_NAME"
        return 0
    else
        print_warning "Binary download failed, will build from source"
        return 1
    fi
}

# Build from source
build_from_source() {
    print_info "Building from source..."
    
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    # Download source
    print_info "Downloading source code..."
    if [ "$VERSION" = "main" ]; then
        curl -fsSL "${GITHUB_REPO}/archive/refs/heads/main.tar.gz" -o source.tar.gz
    else
        curl -fsSL "${GITHUB_REPO}/archive/refs/tags/${VERSION}.tar.gz" -o source.tar.gz
    fi
    
    # Extract
    tar -xzf source.tar.gz
    cd "${REPO_NAME}-"*
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required to build from source"
        exit 1
    fi
    
    # Install dependencies
    print_info "Installing dependencies..."
    if command -v pip3 &> /dev/null; then
        pip3 install --user pillow pyinstaller
    else
        python3 -m pip install --user pillow pyinstaller
    fi
    
    # Build
    print_info "Building binary..."
    if [ -f "build.sh" ]; then
        bash build.sh
    else
        python3 -m PyInstaller \
            --name="${BINARY_NAME}" \
            --onefile \
            --windowed \
            --noconsole \
            --hidden-import=PIL._tkinter_finder \
            main.py
    fi
    
    # Install
    if [ -f "dist/${BINARY_NAME}" ]; then
        mkdir -p "$INSTALL_DIR"
        cp "dist/${BINARY_NAME}" "$INSTALL_DIR/$BINARY_NAME"
        chmod +x "$INSTALL_DIR/$BINARY_NAME"
        print_success "Binary installed to $INSTALL_DIR/$BINARY_NAME"
    else
        print_error "Build failed - binary not found"
        exit 1
    fi
    
    # Cleanup
    cd ~
    rm -rf "$temp_dir"
}

# Configure PATH
configure_path() {
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        print_warning "$INSTALL_DIR is not in your PATH"
        
        local shell_rc=""
        if [ -n "$BASH_VERSION" ] && [ -f "$HOME/.bashrc" ]; then
            shell_rc="$HOME/.bashrc"
        elif [ -n "$ZSH_VERSION" ] && [ -f "$HOME/.zshrc" ]; then
            shell_rc="$HOME/.zshrc"
        elif [ -f "$HOME/.profile" ]; then
            shell_rc="$HOME/.profile"
        fi
        
        if [ -n "$shell_rc" ]; then
            if ! grep -q "export PATH.*$INSTALL_DIR" "$shell_rc"; then
                echo "" >> "$shell_rc"
                echo "# Added by ImageViewer installer" >> "$shell_rc"
                echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$shell_rc"
                print_success "Added to $shell_rc"
                print_info "Run: source $shell_rc"
                print_info "Or restart your terminal"
            fi
        else
            print_warning "Could not find shell config file"
            print_info "Add this to your shell config:"
            echo "  export PATH=\"\$PATH:$INSTALL_DIR\""
        fi
    else
        print_success "$INSTALL_DIR is already in PATH"
    fi
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    if [ -x "$INSTALL_DIR/$BINARY_NAME" ]; then
        print_success "ImageViewer installed successfully!"
        echo ""
        echo "Usage:"
        echo "  $BINARY_NAME <image_path>"
        echo "  $BINARY_NAME --internet <image_url>"
        echo ""
        
        if [[ ":$PATH:" == *":$INSTALL_DIR:"* ]]; then
            print_success "You can now run: $BINARY_NAME"
        else
            print_warning "Add $INSTALL_DIR to your PATH to run from anywhere"
        fi
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

# Main installation flow
main() {
    echo "╔════════════════════════════════════════════╗"
    echo "║      ImageViewer Web Installer             ║"
    echo "║   Copyright (c) 2024 Akshat Kotpalliwar    ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    
    detect_platform
    check_requirements
    get_latest_version
    
    if [ "$BUILD_FROM_SOURCE" = true ]; then
        build_from_source
    else
        if ! install_binary; then
            build_from_source
        fi
    fi
    
    configure_path
    verify_installation
}

# Run main
main "$@"

