#!/bin/bash
# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

set -e

REPO="IntegerAlex/advance-image-viewer"
BINARY_NAME="imageviewer"
VERSION=$(grep '^version =' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
TAG="v${VERSION}"
LATEST_TAG="latest"

echo "========================================="
echo "Building release for advance-image-viewer"
echo "Version: ${VERSION}"
echo "Tag: ${TAG}"
echo "========================================="

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

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
ASSET_NAME="${BINARY_NAME}-${OS}-${ARCH}"

echo "Building for: ${OS} ${ARCH}"
echo "Asset name: ${ASSET_NAME}"

# Clean previous builds
echo ""
echo "Cleaning previous builds..."
rm -rf build dist

# Build the binary
echo ""
echo "Building binary..."
python3 build.py --clean

# Check if binary was created
BINARY_PATH="dist/${BINARY_NAME}"
if [ ! -f "$BINARY_PATH" ]; then
    echo "Error: Binary not found at ${BINARY_PATH}"
    exit 1
fi

echo "Binary created: ${BINARY_PATH}"

# Create release directory
RELEASE_DIR="release"
mkdir -p "$RELEASE_DIR"

# Copy binary with platform-specific name
RELEASE_BINARY="${RELEASE_DIR}/${ASSET_NAME}"
cp "$BINARY_PATH" "$RELEASE_BINARY"
chmod +x "$RELEASE_BINARY"

echo "Release binary prepared: ${RELEASE_BINARY}"

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo ""
    echo "Warning: Tag ${TAG} already exists"
    read -p "Delete existing tag and release? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Delete local tag
        git tag -d "$TAG" 2>/dev/null || true
        # Delete remote tag
        gh release delete "$TAG" --yes 2>/dev/null || true
        git push origin ":refs/tags/${TAG}" 2>/dev/null || true
    else
        echo "Aborted"
        exit 1
    fi
fi

# Check if latest tag exists
if git rev-parse "$LATEST_TAG" >/dev/null 2>&1; then
    echo "Deleting existing 'latest' tag..."
    git tag -d "$LATEST_TAG" 2>/dev/null || true
    gh release delete "$LATEST_TAG" --yes 2>/dev/null || true
    git push origin ":refs/tags/${LATEST_TAG}" 2>/dev/null || true
fi

# Create git tag
echo ""
echo "Creating git tag: ${TAG}"
git tag -a "$TAG" -m "Release ${VERSION}"

# Create latest tag pointing to same commit
echo "Creating git tag: ${LATEST_TAG}"
git tag -a "$LATEST_TAG" -m "Latest release"

# Push tags
echo ""
echo "Pushing tags to remote..."
git push origin "$TAG"
git push origin "$LATEST_TAG"

# Create GitHub release
echo ""
echo "Creating GitHub release: ${TAG}"
RELEASE_NOTES="## advance-image-viewer ${VERSION}

An opiniated imageviewer (its a viewer not editor) with AI.

### Installation

#### Linux/macOS
\`\`\`bash
curl -fsSL https://raw.githubusercontent.com/${REPO}/master/installer.sh | bash
\`\`\`

#### Windows
\`\`\`powershell
Invoke-WebRequest -Uri \"https://raw.githubusercontent.com/${REPO}/master/installer.ps1\" -OutFile installer.ps1
.\installer.ps1
\`\`\`

### Changes
See [CHANGELOG.md](CHANGELOG.md) for details."

gh release create "$TAG" \
    --title "advance-image-viewer ${VERSION}" \
    --notes "$RELEASE_NOTES" \
    "$RELEASE_BINARY"

# Create latest release
echo ""
echo "Creating GitHub release: ${LATEST_TAG}"
gh release create "$LATEST_TAG" \
    --title "advance-image-viewer Latest" \
    --notes "$RELEASE_NOTES" \
    "$RELEASE_BINARY"

echo ""
echo "========================================="
echo "Release created successfully!"
echo "Tag: ${TAG}"
echo "Latest tag: ${LATEST_TAG}"
echo "Asset: ${ASSET_NAME}"
echo "========================================="
echo ""
echo "View release: https://github.com/${REPO}/releases/tag/${TAG}"
echo "View latest: https://github.com/${REPO}/releases/tag/${LATEST_TAG}"

