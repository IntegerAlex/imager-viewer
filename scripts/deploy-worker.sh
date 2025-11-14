#!/usr/bin/env bash
# Deploy ImageViewer Cloudflare Worker
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <akshatkot@gmail.com>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    print_error "Wrangler CLI is not installed"
    print_info "Install with: npm install -g wrangler"
    exit 1
fi

# Check if authenticated
if ! wrangler whoami &> /dev/null; then
    print_error "Not authenticated with Cloudflare"
    print_info "Run: wrangler auth login"
    exit 1
fi

# Change to cloudflare directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WORKER_DIR="$PROJECT_ROOT/cloudflare"

if [[ ! -d "$WORKER_DIR" ]]; then
    print_error "Cloudflare directory not found: $WORKER_DIR"
    exit 1
fi

cd "$WORKER_DIR"

print_info "Deploying ImageViewer Cloudflare Worker..."

# Get worker name for URL construction
WORKER_NAME=$(grep '^name =' wrangler.toml | sed 's/name = "\(.*\)"/\1/')
if [[ -z "$WORKER_NAME" ]]; then
    WORKER_NAME="imageviewer-installer"
fi

# Deploy the worker and capture output
print_info "Deploying ImageViewer Cloudflare Worker..."
DEPLOY_OUTPUT=$(wrangler deploy 2>&1)
DEPLOY_EXIT_CODE=$?

if [[ $DEPLOY_EXIT_CODE -eq 0 ]]; then
    print_success "Worker deployed successfully!"

    # Extract URL from deployment output
    WORKER_URL=$(echo "$DEPLOY_OUTPUT" | grep -o 'https://[^[:space:]]*' | head -1)

    if [[ -z "$WORKER_URL" ]]; then
        # Fallback: construct URL from worker name
        WORKER_URL="https://${WORKER_NAME}.workers.dev"
        print_info "Constructed URL: $WORKER_URL"
    fi
else
    print_error "Failed to deploy worker"
    echo "$DEPLOY_OUTPUT"
    exit 1
fi

# Test the deployment
if [[ -n "$WORKER_URL" ]]; then
    print_info "Testing deployment at $WORKER_URL..."
    if curl -fsSL "${WORKER_URL}/health" &> /dev/null; then
        print_success "Worker is responding correctly!"
        print_info "Installation URLs:"
        print_info "  Linux/macOS: curl -fsSL ${WORKER_URL}/install.sh | bash"
        print_info "  Windows: irm ${WORKER_URL}/install.ps1 | iex"
    else
        print_warning "Worker deployed but health check failed"
        print_info "You can still test manually: curl ${WORKER_URL}/health"
    fi
else
    print_warning "Could not determine worker URL for testing"
    print_info "Check your Cloudflare dashboard for the deployed worker URL"
fi
