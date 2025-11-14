# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>
#
# Web installer script for ImageViewer (Windows)
# Install with: irm image-viewer.<domain>/install.ps1 | iex

#Requires -Version 5.0

$ErrorActionPreference = "Stop"

# Configuration
$RepoOwner = "akshat"
$RepoName = "imageviewer"
$GithubRepo = "https://github.com/$RepoOwner/$RepoName"
$BinaryName = "imageviewer.exe"
$InstallDir = "$env:LOCALAPPDATA\Programs\imageviewer"

# Helper functions
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Type = "Info"
    )
    
    $color = switch ($Type) {
        "Info" { "Cyan" }
        "Success" { "Green" }
        "Warning" { "Yellow" }
        "Error" { "Red" }
        default { "White" }
    }
    
    Write-Host "[$Type] $Message" -ForegroundColor $color
}

# Detect platform
function Get-Platform {
    $arch = [System.Environment]::Is64BitOperatingSystem
    
    if ($arch) {
        return "windows-x86_64"
    } else {
        return "windows-x86"
    }
    
    Write-ColorOutput "Detected platform: $platform" "Info"
}

# Check requirements
function Test-Requirements {
    $missing = @()
    
    # Check for curl or wget
    $hasCurl = Get-Command curl -ErrorAction SilentlyContinue
    $hasWget = Get-Command wget -ErrorAction SilentlyContinue
    
    if (-not $hasCurl -and -not $hasWget) {
        Write-ColorOutput "Warning: Neither curl nor wget found. Using PowerShell's Invoke-WebRequest" "Warning"
    }
    
    # Check for Python (needed for building from source)
    $hasPython = Get-Command python -ErrorAction SilentlyContinue
    if (-not $hasPython) {
        Write-ColorOutput "Warning: Python not found. Will only attempt binary installation" "Warning"
    }
    
    return $true
}

# Get latest version
function Get-LatestVersion {
    Write-ColorOutput "Fetching latest release..." "Info"
    
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$RepoOwner/$RepoName/releases/latest"
        $version = $response.tag_name
        
        if ($version) {
            Write-ColorOutput "Latest version: $version" "Info"
            return @{
                Version = $version
                BuildFromSource = $false
            }
        }
    } catch {
        Write-ColorOutput "No release found, will build from source" "Warning"
    }
    
    return @{
        Version = "main"
        BuildFromSource = $true
    }
}

# Download and install binary
function Install-Binary {
    param(
        [string]$Version,
        [string]$Platform
    )
    
    $downloadUrl = "$GithubRepo/releases/download/$Version/$BinaryName"
    $tempFile = "$env:TEMP\$BinaryName"
    
    Write-ColorOutput "Downloading binary from $downloadUrl" "Info"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempFile -UseBasicParsing
        
        # Create install directory
        if (-not (Test-Path $InstallDir)) {
            New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
        }
        
        # Install binary
        $installPath = Join-Path $InstallDir $BinaryName
        Move-Item -Path $tempFile -Destination $installPath -Force
        
        Write-ColorOutput "Binary installed to $installPath" "Success"
        return $true
    } catch {
        Write-ColorOutput "Binary download failed: $_" "Warning"
        return $false
    }
}

# Build from source
function Build-FromSource {
    param([string]$Version)
    
    Write-ColorOutput "Building from source..." "Info"
    
    # Check for Python
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-ColorOutput "Python is required to build from source" "Error"
        throw "Python not found"
    }
    
    $tempDir = Join-Path $env:TEMP "imageviewer-build"
    if (Test-Path $tempDir) {
        Remove-Item -Path $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    Push-Location $tempDir
    
    try {
        # Download source
        Write-ColorOutput "Downloading source code..." "Info"
        $sourceUrl = if ($Version -eq "main") {
            "$GithubRepo/archive/refs/heads/main.zip"
        } else {
            "$GithubRepo/archive/refs/tags/$Version.zip"
        }
        
        $zipFile = Join-Path $tempDir "source.zip"
        Invoke-WebRequest -Uri $sourceUrl -OutFile $zipFile -UseBasicParsing
        
        # Extract
        Expand-Archive -Path $zipFile -DestinationPath $tempDir
        $sourceDir = Get-ChildItem -Path $tempDir -Directory | Select-Object -First 1
        Set-Location $sourceDir.FullName
        
        # Install dependencies
        Write-ColorOutput "Installing dependencies..." "Info"
        python -m pip install --user pillow pyinstaller
        
        # Build
        Write-ColorOutput "Building binary..." "Info"
        if (Test-Path "build.bat") {
            & .\build.bat
        } else {
            python -m PyInstaller `
                --name=$($BinaryName -replace '\.exe$', '') `
                --onefile `
                --windowed `
                --noconsole `
                --hidden-import=PIL._tkinter_finder `
                main.py
        }
        
        # Install
        $builtBinary = Join-Path "dist" $BinaryName
        if (Test-Path $builtBinary) {
            if (-not (Test-Path $InstallDir)) {
                New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
            }
            
            Copy-Item -Path $builtBinary -Destination (Join-Path $InstallDir $BinaryName) -Force
            Write-ColorOutput "Binary installed to $(Join-Path $InstallDir $BinaryName)" "Success"
        } else {
            throw "Build failed - binary not found"
        }
    } finally {
        Pop-Location
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Configure PATH
function Set-EnvironmentPath {
    $currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    
    if ($currentPath -notlike "*$InstallDir*") {
        Write-ColorOutput "Adding $InstallDir to PATH..." "Info"
        
        $newPath = if ($currentPath) {
            "$currentPath;$InstallDir"
        } else {
            $InstallDir
        }
        
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        
        # Update current session
        $env:PATH = "$env:PATH;$InstallDir"
        
        Write-ColorOutput "Added to PATH" "Success"
        Write-ColorOutput "Please restart your terminal or PowerShell session" "Warning"
    } else {
        Write-ColorOutput "$InstallDir is already in PATH" "Success"
    }
}

# Verify installation
function Test-Installation {
    Write-ColorOutput "Verifying installation..." "Info"
    
    $installPath = Join-Path $InstallDir $BinaryName
    
    if (Test-Path $installPath) {
        Write-ColorOutput "ImageViewer installed successfully!" "Success"
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  $($BinaryName -replace '\.exe$', '') <image_path>"
        Write-Host "  $($BinaryName -replace '\.exe$', '') --internet <image_url>"
        Write-Host ""
        
        $inPath = $env:PATH -split ';' | Where-Object { $_ -eq $InstallDir }
        if ($inPath) {
            Write-ColorOutput "You can now run: $($BinaryName -replace '\.exe$', '')" "Success"
        } else {
            Write-ColorOutput "Restart your terminal to use the command" "Warning"
        }
    } else {
        Write-ColorOutput "Installation verification failed" "Error"
        throw "Installation failed"
    }
}

# Main installation flow
function Install-ImageViewer {
    Write-Host "╔════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      ImageViewer Web Installer             ║" -ForegroundColor Cyan
    Write-Host "║   Copyright (c) 2024 Akshat Kotpalliwar    ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        $platform = Get-Platform
        Test-Requirements | Out-Null
        
        $versionInfo = Get-LatestVersion
        
        if ($versionInfo.BuildFromSource) {
            Build-FromSource -Version $versionInfo.Version
        } else {
            $installed = Install-Binary -Version $versionInfo.Version -Platform $platform
            if (-not $installed) {
                Write-ColorOutput "Falling back to building from source..." "Warning"
                Build-FromSource -Version $versionInfo.Version
            }
        }
        
        Set-EnvironmentPath
        Test-Installation
        
        Write-ColorOutput "Installation complete!" "Success"
    } catch {
        Write-ColorOutput "Installation failed: $_" "Error"
        Write-ColorOutput $_.ScriptStackTrace "Error"
        exit 1
    }
}

# Run installation
Install-ImageViewer

