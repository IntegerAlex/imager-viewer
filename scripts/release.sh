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
echo ""
echo "⚠️  REMINDER: Update CHANGELOG.md before creating releases!"
echo "   - Move unreleased changes to version section"
echo "   - Add new [Unreleased] section for future changes"
echo ""
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
python3 scripts/build.py --clean

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

# Check if tag already exists locally
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo ""
    echo "Tag ${TAG} already exists locally"
else
    # Create git tag
    echo ""
    echo "Creating git tag: ${TAG}"
    git tag -a "$TAG" -m "Release ${VERSION}"

    # Push tag
    echo "Pushing tag to remote..."
    git push origin "$TAG"
fi

# Check if release exists on GitHub
if gh release view "$TAG" >/dev/null 2>&1; then
    echo ""
    echo "Release ${TAG} already exists, uploading asset..."
    gh release upload "$TAG" "$RELEASE_BINARY"
else
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
fi

# Handle latest tag separately
echo ""
if git rev-parse "$LATEST_TAG" >/dev/null 2>&1; then
    echo "Updating 'latest' tag..."
    git tag -d "$LATEST_TAG" 2>/dev/null || true
fi

git tag -f "$LATEST_TAG" -m "Latest release"
git push -f origin "$LATEST_TAG"

# Update or create latest release
if gh release view "$LATEST_TAG" >/dev/null 2>&1; then
    echo "Updating latest release with new asset..."
    gh release upload "$LATEST_TAG" "$RELEASE_BINARY"
else
    echo "Creating GitHub release: ${LATEST_TAG}"
    gh release create "$LATEST_TAG" \
        --title "advance-image-viewer Latest" \
        --notes "$RELEASE_NOTES" \
        "$RELEASE_BINARY"
fi

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

