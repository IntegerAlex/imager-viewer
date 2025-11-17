# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

$ErrorActionPreference = "Stop"

$REPO = "IntegerAlex/advance-image-viewer"
$BINARY_NAME = "imageviewer.exe"
$versionLine = Select-String -Path "pyproject.toml" -Pattern '^version ='
if ($versionLine) {
    if ($versionLine.Line -match 'version = "([^"]+)"') {
        $VERSION = $matches[1]
    } else {
        Write-Host "Error: Could not parse version from pyproject.toml" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Error: Could not find version in pyproject.toml" -ForegroundColor Red
    exit 1
}
$TAG = "v$VERSION"
$LATEST_TAG = "latest"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Building release for advance-image-viewer" -ForegroundColor Cyan
Write-Host "Version: $VERSION" -ForegroundColor Cyan
Write-Host "Tag: $TAG" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# Check if we're in a git repository
if (-not (Test-Path .git)) {
    Write-Host "Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Check if gh CLI is installed
try {
    $null = Get-Command gh -ErrorAction Stop
} catch {
    Write-Host "Error: GitHub CLI (gh) is not installed" -ForegroundColor Red
    Write-Host "Install it from: https://cli.github.com/" -ForegroundColor Yellow
    exit 1
}

# Check if user is authenticated
try {
    gh auth status | Out-Null
} catch {
    Write-Host "Error: Not authenticated with GitHub CLI" -ForegroundColor Red
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

# Detect architecture
$ARCH = $env:PROCESSOR_ARCHITECTURE
if ($env:PROCESSOR_ARCHITEW6432) {
    $ARCH = $env:PROCESSOR_ARCHITEW6432
}

if ($ARCH -eq "AMD64") {
    $ARCH = "x86_64"
} elseif ($ARCH -eq "ARM64") {
    $ARCH = "aarch64"
} else {
    Write-Host "Unsupported architecture: $ARCH" -ForegroundColor Red
    exit 1
}

$OS = "windows"
$ASSET_NAME = "${BINARY_NAME}-${OS}-${ARCH}.exe"

Write-Host "Building for: $OS $ARCH" -ForegroundColor Green
Write-Host "Asset name: $ASSET_NAME" -ForegroundColor Green

# Clean previous builds
Write-Host ""
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Build the binary
Write-Host ""
Write-Host "Building binary..." -ForegroundColor Yellow
python build.py --clean

# Check if binary was created
$BINARY_PATH = "dist\${BINARY_NAME}"
if (-not (Test-Path $BINARY_PATH)) {
    Write-Host "Error: Binary not found at $BINARY_PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Binary created: $BINARY_PATH" -ForegroundColor Green

# Create release directory
$RELEASE_DIR = "release"
if (-not (Test-Path $RELEASE_DIR)) {
    New-Item -ItemType Directory -Path $RELEASE_DIR | Out-Null
}

# Copy binary with platform-specific name
$RELEASE_BINARY = Join-Path $RELEASE_DIR $ASSET_NAME
Copy-Item $BINARY_PATH $RELEASE_BINARY -Force

Write-Host "Release binary prepared: $RELEASE_BINARY" -ForegroundColor Green

# Check if tag already exists locally
try {
    $null = git rev-parse "$TAG" 2>$null
    Write-Host ""
    Write-Host "Tag $TAG already exists locally" -ForegroundColor Green
} catch {
    # Create git tag
    Write-Host ""
    Write-Host "Creating git tag: $TAG" -ForegroundColor Yellow
    git tag -a "$TAG" -m "Release $VERSION"

    # Push tag
    Write-Host "Pushing tag to remote..." -ForegroundColor Yellow
    git push origin "$TAG"
}

# Check if release exists on GitHub
try {
    gh release view "$TAG" | Out-Null
    Write-Host ""
    Write-Host "Release $TAG already exists, uploading asset..." -ForegroundColor Yellow
    gh release upload "$TAG" "$RELEASE_BINARY"
} catch {
    Write-Host ""
    Write-Host "Creating GitHub release: $TAG" -ForegroundColor Yellow

    $RELEASE_NOTES = @"
## advance-image-viewer $VERSION

An opiniated imageviewer (its a viewer not editor) with AI.

### Installation

#### Linux/macOS
````bash
curl -fsSL https://raw.githubusercontent.com/$REPO/master/installer.sh | bash
````

#### Windows
````powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/$REPO/master/installer.ps1" -OutFile installer.ps1
.\installer.ps1
````

### Changes
See [CHANGELOG.md](CHANGELOG.md) for details.
"@

    gh release create "$TAG" `
        --title "advance-image-viewer $VERSION" `
        --notes $RELEASE_NOTES `
        "$RELEASE_BINARY"
}

# Handle latest tag separately
Write-Host ""
try {
    $null = git rev-parse "$LATEST_TAG" 2>$null
    Write-Host "Updating 'latest' tag..." -ForegroundColor Yellow
    git tag -d "$LATEST_TAG" 2>$null
} catch {
    # Tag doesn't exist
}

git tag -f "$LATEST_TAG" -m "Latest release"
git push -f origin "$LATEST_TAG"

# Update or create latest release
try {
    gh release view "$LATEST_TAG" | Out-Null
    Write-Host "Updating latest release with new asset..." -ForegroundColor Yellow
    gh release upload "$LATEST_TAG" "$RELEASE_BINARY"
} catch {
    Write-Host "Creating GitHub release: $LATEST_TAG" -ForegroundColor Yellow
    gh release create "$LATEST_TAG" `
        --title "advance-image-viewer Latest" `
        --notes $RELEASE_NOTES `
        "$RELEASE_BINARY"
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Release created successfully!" -ForegroundColor Green
Write-Host "Tag: $TAG" -ForegroundColor Green
Write-Host "Latest tag: $LATEST_TAG" -ForegroundColor Green
Write-Host "Asset: $ASSET_NAME" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "View release: https://github.com/$REPO/releases/tag/$TAG" -ForegroundColor Cyan
Write-Host "View latest: https://github.com/$REPO/releases/tag/$LATEST_TAG" -ForegroundColor Cyan

