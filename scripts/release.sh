#!/usr/bin/env bash
set -Eeuo pipefail

# Create a GitHub release with built binary
# Copyright (C) 2024 Akshat Kotpalliwar <akshatkot@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

# Security: Validate ROOT_DIR
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)" || {
  echo "❌ Failed to determine ROOT_DIR" >&2
  exit 1
}

[[ -d "$ROOT_DIR" ]] || {
  echo "❌ Invalid ROOT_DIR: $ROOT_DIR" >&2
  exit 1
}

cd "$ROOT_DIR"

# Check for gh CLI
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) is not installed." >&2
  echo "Install it: https://cli.github.com/" >&2
  echo "  macOS:   brew install gh" >&2
  echo "  Linux:   See https://github.com/cli/cli/blob/trunk/docs/install_linux.md" >&2
  exit 1
fi

# Check if logged in
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ Not logged in to GitHub." >&2
  echo "Run: gh auth login" >&2
  exit 1
fi

# Get version from pyproject.toml
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ python3 is required" >&2
  exit 1
fi

VERSION=$(python3 -c "import tomllib; f=open('pyproject.toml', 'rb'); data=tomllib.load(f); f.close(); print(data['project']['version'])" 2>/dev/null) || {
  echo "❌ Could not extract version from pyproject.toml" >&2
  exit 1
}

# Security: Validate version format (semantic versioning)
if [[ ! "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "❌ Invalid version format: $VERSION (expected: X.Y.Z)" >&2
  exit 1
fi

TAG="v${VERSION}"

echo "🚀 Creating release ${TAG}..."

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
  echo "❌ Tag ${TAG} already exists." >&2
  echo "Update version in pyproject.toml or delete the tag:" >&2
  echo "  git tag -d ${TAG}" >&2
  echo "  git push origin :refs/tags/${TAG}" >&2
  exit 1
fi

# Build binaries for multiple platforms
echo "📦 Building binaries..."

# Build Linux/macOS binary
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
  echo "Building for current platform (Linux/macOS)..."
  ./scripts/build.sh --type exe
fi

# Build Windows binary (cross-compilation)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "Building Windows binary..."
  # Note: Cross-compilation requires wine and Windows Python
  # For now, we'll build what's available
fi

# Check for binaries
BINARIES=()
if [[ -f dist/imageviewer ]]; then
  BINARIES+=("dist/imageviewer")
fi
if [[ -f dist/imageviewer.exe ]]; then
  BINARIES+=("dist/imageviewer.exe")
fi

# Also check for any other build artifacts
if [[ -d dist ]] && [[ ${#BINARIES[@]} -eq 0 ]]; then
  for file in dist/*; do
    if [[ -f "$file" ]] && [[ -x "$file" || "$file" == *.exe ]]; then
      BINARIES+=("$file")
    fi
  done
fi

if [[ ${#BINARIES[@]} -eq 0 ]]; then
  echo "❌ No binaries found in dist/ directory" >&2
  echo "Run ./scripts/build.sh --type exe first" >&2
  exit 1
fi

echo "📦 Found ${#BINARIES[@]} binary(ies) to upload: ${BINARIES[*]}"

# Create SHA256 checksums for verification
echo "🔐 Creating SHA256 checksums..."
for binary in "${BINARIES[@]}"; do
  if [[ -f "$binary" ]]; then
    sha256sum "$binary" > "${binary}.sha256"
    BINARIES+=("${binary}.sha256")
  fi
done

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Create and push tag
echo "🏷️  Creating tag ${TAG}..."
git tag -a "${TAG}" -m "Release ${TAG}"
git push origin "${TAG}"

# Generate release notes
RELEASE_NOTES="Release ${TAG}

## Installation

**Remote Installation (Recommended):**

**Windows:**
\`\`\`powershell
irm https://imageviewer-installer.inquiry-akshatkotpalliwar.workers.dev/install.ps1 | iex
\`\`\`

**Linux/macOS:**
\`\`\`bash
curl -fsSL https://imageviewer-installer.inquiry-akshatkotpalliwar.workers.dev/install.sh | bash
\`\`\`

**Manual Installation:**
Or download the binary directly and place it on your PATH.

## What is ImageViewer?

ImageViewer is a simple, memory-efficient image viewer with cursor-focused zoom for Linux, macOS, and Windows.

### Features
- Memory-efficient image viewing
- Cursor-focused zoom (zoom at mouse position)
- Keyboard and mouse controls
- Support for various image formats
- Cross-platform compatibility

### Controls
- **Mouse wheel**: Zoom in/out at cursor position
- **+ / =**: Zoom in at cursor
- **-**: Zoom out at cursor
- **0 / Escape**: Reset zoom to 1:1
- **Arrow keys**: Pan image
- **Left mouse drag**: Pan image
- **Middle mouse drag**: Pan image

## Changes

See commit history for details.
"

# Create GitHub release
echo "📝 Creating GitHub release..."
gh release create "${TAG}" \
  --title "ImageViewer ${TAG}" \
  --notes "${RELEASE_NOTES}" \
  --latest \
  "${BINARIES[@]}"

echo ""
echo "✅ Release ${TAG} created successfully!"
echo "📦 Binary(ies) uploaded: ${BINARIES[*]}"
echo "🔗 View at: $(gh release view ${TAG} --json url -q .url)"
echo ""

# Show download URLs
for binary in "${BINARIES[@]}"; do
  if [[ "$binary" == dist/imageviewer ]]; then
    echo "📦 Linux/macOS Download URL: https://github.com/IntegerAlex/imager-viewer/releases/download/${TAG}/imageviewer"
  elif [[ "$binary" == dist/imageviewer.exe ]]; then
    echo "📦 Windows Download URL: https://github.com/IntegerAlex/imager-viewer/releases/download/${TAG}/imageviewer.exe"
  fi
done

echo ""
echo "🎉 Remote installer is now ready to use!"
echo "   Linux/macOS: curl -fsSL https://imageviewer-installer.inquiry-akshatkotpalliwar.workers.dev/install.sh | bash"
echo "   Windows:     irm https://imageviewer-installer.inquiry-akshatkotpalliwar.workers.dev/install.ps1 | iex"
