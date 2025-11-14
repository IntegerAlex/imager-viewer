#!/bin/bash
# ImageViewer Installation Script
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_TYPE="user"
PYTHON_VERSION=""
VIRTUAL_ENV=".venv"
VERBOSE=false

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
    echo "Install ImageViewer and its dependencies"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE      Installation type: user, dev, system (default: user)"
    echo "  -p, --python VER     Python version to use (default: auto-detect)"
    echo "  -v, --venv NAME      Virtual environment name (default: .venv)"
    echo "  --verbose            Enable verbose output"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Installation types:"
    echo "  user     Install for current user with virtual environment"
    echo "  dev      Install development dependencies"
    echo "  system   Install system-wide (requires sudo)"
    echo ""
    echo "Examples:"
    echo "  $0                    # User install with virtual environment"
    echo "  $0 --type dev         # Development install"
    echo "  $0 --python 3.12      # Use specific Python version"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            INSTALL_TYPE="$2"
            shift 2
            ;;
        -p|--python)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -v|--venv)
            VIRTUAL_ENV="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get Python executable
get_python_exe() {
    if [ -n "$PYTHON_VERSION" ]; then
        if command_exists "python$PYTHON_VERSION"; then
            echo "python$PYTHON_VERSION"
        else
            print_error "Python $PYTHON_VERSION not found"
            exit 1
        fi
    else
        # Try different Python versions in order of preference
        for py in python3.12 python3.11 python3.10 python3.9 python3.8 python3; do
            if command_exists "$py"; then
                echo "$py"
                return
            fi
        done
        print_error "No suitable Python version found"
        exit 1
    fi
}

# Function to check system dependencies
check_system_deps() {
    print_info "Checking system dependencies..."

    local missing_deps=()

    # Check for required commands
    for cmd in curl wget; do
        if ! command_exists "$cmd"; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_warning "Missing system dependencies: ${missing_deps[*]}"
        print_info "Please install them using your package manager:"
        echo "  Ubuntu/Debian: sudo apt-get install curl wget"
        echo "  macOS: brew install curl wget"
        echo "  CentOS/RHEL: sudo yum install curl wget"
    fi
}

# Function to install with uv (modern Python package manager)
install_with_uv() {
    local python_exe="$1"

    print_info "Installing with uv..."

    if ! command_exists "uv"; then
        print_info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    # Create virtual environment if it doesn't exist
    if [ ! -d "$VIRTUAL_ENV" ]; then
        print_info "Creating virtual environment: $VIRTUAL_ENV"
        uv venv "$VIRTUAL_ENV"
    fi

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Install dependencies
    print_info "Installing dependencies..."
    uv sync

    if [ "$INSTALL_TYPE" = "dev" ]; then
        print_info "Installing development dependencies..."
        uv sync --dev
    fi

    print_success "Dependencies installed successfully"
}

# Function to install with pip
install_with_pip() {
    local python_exe="$1"

    print_info "Installing with pip..."

    # Create virtual environment if it doesn't exist
    if [ ! -d "$VIRTUAL_ENV" ]; then
        print_info "Creating virtual environment: $VIRTUAL_ENV"
        "$python_exe" -m venv "$VIRTUAL_ENV"
    fi

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Upgrade pip
    print_info "Upgrading pip..."
    python -m pip install --upgrade pip

    # Install dependencies
    print_info "Installing dependencies..."
    if [ "$INSTALL_TYPE" = "dev" ]; then
        pip install -e ".[dev]"
    else
        pip install -e .
    fi

    print_success "Dependencies installed successfully"
}

# Function to install system-wide
install_system_wide() {
    print_info "Installing system-wide (this may require sudo)..."

    if [ "$INSTALL_TYPE" = "dev" ]; then
        pip install -e ".[dev]"
    else
        pip install .
    fi

    print_success "System-wide installation completed"
}

# Function to verify installation
verify_installation() {
    print_info "Verifying installation..."

    # Activate virtual environment if it exists
    if [ -f "$VIRTUAL_ENV/bin/activate" ]; then
        source "$VIRTUAL_ENV/bin/activate"
    fi

    # Test import
    if python -c "from src.image_viewer import ImageViewer; print('ImageViewer import successful')"; then
        print_success "Installation verified successfully"
    else
        print_error "Installation verification failed"
        exit 1
    fi
}

# Function to show post-installation instructions
show_post_install() {
    echo ""
    print_info "Post-installation setup:"
    echo ""
    echo "To activate the virtual environment:"
    echo "  source $VIRTUAL_ENV/bin/activate"
    echo ""
    echo "To run ImageViewer:"
    echo "  python main.py <image_path>"
    echo "  python main.py --internet <image_url>"
    echo ""
    echo "To build the application:"
    echo "  ./build.sh"
    echo ""
    echo "To deactivate the virtual environment:"
    echo "  deactivate"
}

# Main installation function
main() {
    print_info "Starting ImageViewer installation..."
    print_info "Installation type: $INSTALL_TYPE"

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi

    # Check system dependencies
    check_system_deps

    # Get Python executable
    PYTHON_EXE=$(get_python_exe)
    print_info "Using Python: $PYTHON_EXE"

    case $INSTALL_TYPE in
        "user")
            # Try uv first, fall back to pip
            if command_exists "uv" || curl -LsSf https://astral.sh/uv/install.sh >/dev/null 2>&1; then
                install_with_uv "$PYTHON_EXE"
            else
                install_with_pip "$PYTHON_EXE"
            fi
            ;;
        "dev")
            # Always use uv for development to ensure all dev dependencies
            install_with_uv "$PYTHON_EXE"
            ;;
        "system")
            install_system_wide
            ;;
        *)
            print_error "Invalid installation type: $INSTALL_TYPE"
            usage
            exit 1
            ;;
    esac

    # Verify installation
    verify_installation

    print_success "ImageViewer installation completed successfully!"
    show_post_install
}

# Run main function
main "$@"
