#!/bin/bash
# ImageViewer Development Setup Script
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
VIRTUAL_ENV=".venv"
PYTHON_VERSION=""
VERBOSE=false
SKIP_TESTS=false

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
    echo "Set up ImageViewer development environment"
    echo ""
    echo "Options:"
    echo "  -p, --python VER     Python version to use (default: auto-detect)"
    echo "  -v, --venv NAME      Virtual environment name (default: .venv)"
    echo "  --verbose            Enable verbose output"
    echo "  --skip-tests         Skip running tests after setup"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Standard development setup"
    echo "  $0 --python 3.12      # Use specific Python version"
    echo "  $0 --skip-tests       # Skip test execution"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
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
        --skip-tests)
            SKIP_TESTS=true
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

# Function to install development tools
install_dev_tools() {
    print_info "Installing development tools..."

    # Install uv if not present
    if ! command_exists "uv"; then
        print_info "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
    fi

    # Install pre-commit if not present
    if ! command_exists "pre-commit"; then
        print_info "Installing pre-commit..."
        pip install pre-commit
    fi
}

# Function to setup virtual environment
setup_venv() {
    local python_exe="$1"

    print_info "Setting up virtual environment..."

    # Remove existing venv if it exists
    if [ -d "$VIRTUAL_ENV" ]; then
        print_warning "Removing existing virtual environment: $VIRTUAL_ENV"
        rm -rf "$VIRTUAL_ENV"
    fi

    # Create new virtual environment
    print_info "Creating virtual environment with $python_exe..."
    uv venv "$VIRTUAL_ENV" --python "$python_exe"

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    print_success "Virtual environment created: $VIRTUAL_ENV"
}

# Function to install dependencies
install_dependencies() {
    print_info "Installing dependencies..."

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Install all dependencies including dev dependencies
    uv sync --dev

    print_success "Dependencies installed"
}

# Function to setup pre-commit hooks
setup_pre_commit() {
    print_info "Setting up pre-commit hooks..."

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Install pre-commit hooks
    pre-commit install

    print_success "Pre-commit hooks installed"
}

# Function to run initial checks
run_checks() {
    print_info "Running initial development checks..."

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Check Python version
    python_version=$(python --version)
    print_info "Python version: $python_version"

    # Check imports
    print_info "Testing imports..."
    python -c "from src.image_viewer import ImageViewer; print('✓ ImageViewer import successful')"

    # Check code compilation
    print_info "Checking code compilation..."
    python -m compileall src/
    print_success "Code compilation check passed"

    # Run basic linting if tools are available
    if command_exists "flake8"; then
        print_info "Running flake8 linting..."
        flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
    fi

    if command_exists "mypy"; then
        print_info "Running mypy type checking..."
        mypy src/ || true
    fi
}

# Function to run tests
run_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        print_info "Skipping tests as requested"
        return
    fi

    print_info "Running tests..."

    # Activate virtual environment
    source "$VIRTUAL_ENV/bin/activate"

    # Run tests if test directory exists
    if [ -d "tests" ]; then
        if command_exists "pytest"; then
            pytest tests/ -v
        else
            print_warning "pytest not found, running basic Python tests..."
            python -m unittest discover tests/
        fi
    else
        print_warning "No tests directory found, skipping tests"
    fi
}

# Function to show development instructions
show_dev_instructions() {
    echo ""
    print_success "Development environment setup completed!"
    echo ""
    print_info "Development workflow:"
    echo ""
    echo "Activate the virtual environment:"
    echo "  source $VIRTUAL_ENV/bin/activate"
    echo ""
    echo "Run the application:"
    echo "  python main.py <image_path>"
    echo ""
    echo "Build the application:"
    echo "  ./build.sh"
    echo ""
    echo "Run tests:"
    echo "  ./run-tests.sh"
    echo ""
    echo "Run linting:"
    echo "  pre-commit run --all-files"
    echo ""
    echo "Deactivate the virtual environment:"
    echo "  deactivate"
    echo ""
    print_info "Available scripts:"
    echo "  ./install.sh     - Install dependencies"
    echo "  ./build.sh       - Build the application"
    echo "  ./dev-setup.sh   - Setup development environment (this script)"
}

# Main setup function
main() {
    print_info "Setting up ImageViewer development environment..."

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi

    # Get Python executable
    PYTHON_EXE=$(get_python_exe)
    print_info "Using Python: $PYTHON_EXE"

    # Install development tools
    install_dev_tools

    # Setup virtual environment
    setup_venv "$PYTHON_EXE"

    # Install dependencies
    install_dependencies

    # Setup pre-commit hooks
    setup_pre_commit

    # Run initial checks
    run_checks

    # Run tests
    run_tests

    # Show instructions
    show_dev_instructions
}

# Run main function
main "$@"
