#!/bin/bash
# ImageViewer Test Runner Script
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
VIRTUAL_ENV=".venv"

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
    echo "Run ImageViewer tests"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE      Test type: all, unit, integration, lint (default: all)"
    echo "  -v, --verbose        Enable verbose output"
    echo "  -c, --coverage       Generate coverage report"
    echo "  --venv NAME          Virtual environment name (default: .venv)"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Test types:"
    echo "  all         Run all tests (unit, integration, lint)"
    echo "  unit        Run unit tests only"
    echo "  integration Run integration tests only"
    echo "  lint        Run linting checks only"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 --type unit        # Run unit tests only"
    echo "  $0 --coverage         # Run with coverage report"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        --venv)
            VIRTUAL_ENV="$2"
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "$VIRTUAL_ENV/bin/activate" ]; then
        source "$VIRTUAL_ENV/bin/activate"
    else
        print_error "Virtual environment not found: $VIRTUAL_ENV"
        print_info "Run ./dev-setup.sh first to set up the development environment"
        exit 1
    fi
}

# Function to run unit tests
run_unit_tests() {
    print_info "Running unit tests..."

    if [ -d "tests" ]; then
        if command_exists "pytest"; then
            local pytest_args="-v"
            if [ "$COVERAGE" = true ]; then
                pytest_args="$pytest_args --cov=src --cov-report=html --cov-report=term"
            fi
            if [ "$VERBOSE" = true ]; then
                pytest_args="$pytest_args -s"
            fi

            pytest $pytest_args tests/
        else
            print_warning "pytest not found, using unittest..."
            python -m unittest discover tests/ -v
        fi
    else
        print_warning "No tests directory found"
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_info "Running integration tests..."

    if [ -d "tests/integration" ]; then
        if command_exists "pytest"; then
            local pytest_args="-v -m integration"
            if [ "$COVERAGE" = true ]; then
                pytest_args="$pytest_args --cov=src --cov-report=html --cov-report=term"
            fi
            if [ "$VERBOSE" = true ]; then
                pytest_args="$pytest_args -s"
            fi

            pytest $pytest_args tests/
        else
            print_warning "pytest not found, integration tests require pytest"
        fi
    else
        print_warning "No integration tests found"
    fi
}

# Function to run linting
run_linting() {
    print_info "Running linting checks..."

    # Check code compilation
    print_info "Checking code compilation..."
    python -m compileall src/
    print_success "Code compilation check passed"

    # Run flake8 if available
    if command_exists "flake8"; then
        print_info "Running flake8..."
        flake8 src/ --count --statistics
        if [ $? -eq 0 ]; then
            print_success "Flake8 checks passed"
        fi
    else
        print_warning "flake8 not found, skipping flake8 checks"
    fi

    # Run mypy if available
    if command_exists "mypy"; then
        print_info "Running mypy type checking..."
        mypy src/
        if [ $? -eq 0 ]; then
            print_success "Type checking passed"
        fi
    else
        print_warning "mypy not found, skipping type checking"
    fi

    # Run black check if available
    if command_exists "black"; then
        print_info "Checking code formatting with black..."
        black --check src/
        if [ $? -eq 0 ]; then
            print_success "Code formatting check passed"
        fi
    else
        print_warning "black not found, skipping formatting check"
    fi
}

# Function to run all tests
run_all_tests() {
    print_info "Running all tests..."

    run_linting
    echo ""
    run_unit_tests
    echo ""
    run_integration_tests

    print_success "All tests completed!"
}

# Function to show test results summary
show_summary() {
    if [ "$COVERAGE" = true ] && [ -f "htmlcov/index.html" ]; then
        print_info "Coverage report generated: htmlcov/index.html"
        print_info "Open in browser: python -m http.server 8000 -d htmlcov/"
    fi
}

# Main test function
main() {
    print_info "Starting ImageViewer test suite..."
    print_info "Test type: $TEST_TYPE"

    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ]; then
        print_error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    fi

    # Activate virtual environment
    activate_venv

    case $TEST_TYPE in
        "unit")
            run_unit_tests
            ;;
        "integration")
            run_integration_tests
            ;;
        "lint")
            run_linting
            ;;
        "all")
            run_all_tests
            ;;
        *)
            print_error "Invalid test type: $TEST_TYPE"
            usage
            exit 1
            ;;
    esac

    # Show summary
    show_summary

    print_success "Test execution completed!"
}

# Run main function
main "$@"
