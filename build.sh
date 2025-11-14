#!/bin/bash
# ImageViewer Build Script
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD_TYPE="all"
CLEAN=false
VERBOSE=false
DIST_DIR="dist"
BUILD_DIR="build"

# Function to print colored output
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

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Build ImageViewer application"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE      Build type: all, wheel, exe, app (default: all)"
    echo "  -c, --clean          Clean build directories before building"
    echo "  -v, --verbose        Enable verbose output"
    echo "  -d, --dist DIR       Distribution directory (default: dist)"
    echo "  -b, --build DIR      Build directory (default: build)"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Build types:"
    echo "  all     Build both wheel package and executable"
    echo "  wheel   Build Python wheel package only"
    echo "  exe     Build standalone executable only"
    echo "  app     Build application bundle (macOS only)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Build everything"
    echo "  $0 --type exe         # Build executable only"
    echo "  $0 --clean --verbose  # Clean and build with verbose output"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            shift 2
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dist)
            DIST_DIR="$2"
            shift 2
            ;;
        -b|--build)
            BUILD_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Enable verbose mode
if [ "$VERBOSE" = true ]; then
    set -x
fi

# Function to clean build directories
clean_build() {
    print_info "Cleaning build directories..."
    rm -rf "$BUILD_DIR" "$DIST_DIR" *.spec *.egg-info
    print_success "Build directories cleaned"
}

# Function to build Python wheel
build_wheel() {
    print_info "Building Python wheel package..."
    python -m build --wheel
    print_success "Wheel package built successfully"
}

# Function to build executable
build_executable() {
    print_info "Building standalone executable..."

    # Create executable using PyInstaller
    pyinstaller --clean \
                --workpath "$BUILD_DIR" \
                --distpath "$DIST_DIR" \
                --onefile \
                --noconsole \
                --name imageviewer \
                --hidden-import PIL._tkinter_finder \
                main.py

    print_success "Executable built successfully: $DIST_DIR/imageviewer"
}

# Function to build macOS app bundle
build_app_bundle() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        print_warning "App bundle building is only supported on macOS"
        return
    fi

    print_info "Building macOS app bundle..."

    pyinstaller --clean \
                --workpath "$BUILD_DIR" \
                --distpath "$DIST_DIR" \
                --onedir \
                --noconsole \
                --name "ImageViewer" \
                --hidden-import PIL._tkinter_finder \
                --osx-bundle-identifier "com.akshatkot.imageviewer" \
                main.py

    print_success "App bundle built successfully"
}

# Main build function
main() {
    print_info "Starting ImageViewer build process..."
    print_info "Build type: $BUILD_TYPE"

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi

    # Clean if requested
    if [ "$CLEAN" = true ]; then
        clean_build
    fi

    # Ensure dist directory exists
    mkdir -p "$DIST_DIR"

    case $BUILD_TYPE in
        "wheel")
            build_wheel
            ;;
        "exe")
            build_executable
            ;;
        "app")
            build_app_bundle
            ;;
        "all")
            build_wheel
            build_executable
            ;;
        *)
            print_error "Invalid build type: $BUILD_TYPE"
            usage
            exit 1
            ;;
    esac

    print_success "Build completed successfully!"
    print_info "Output location: $DIST_DIR/"
}

# Run main function
main "$@"
