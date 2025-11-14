# ImageViewer Build Script for Windows
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

param(
    [string]$BuildType = "all",
    [switch]$Clean,
    [switch]$Verbose,
    [string]$DistDir = "dist",
    [string]$BuildDir = "build",
    [switch]$Help
)

# Colors for output (PowerShell doesn't have built-in color constants like bash)
$Colors = @{
    Red = [ConsoleColor]::Red
    Green = [ConsoleColor]::Green
    Yellow = [ConsoleColor]::Yellow
    Blue = [ConsoleColor]::Blue
    White = [ConsoleColor]::White
}

function Write-ColoredOutput {
    param(
        [string]$Color,
        [string]$Message
    )
    $originalColor = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $Colors[$Color]
    Write-Host $Message
    $host.UI.RawUI.ForegroundColor = $originalColor
}

function Write-Info {
    param([string]$Message)
    Write-ColoredOutput "Blue" "[INFO] $Message"
}

function Write-Success {
    param([string]$Message)
    Write-ColoredOutput "Green" "[SUCCESS] $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-ColoredOutput "Yellow" "[WARNING] $Message"
}

function Write-Error {
    param([string]$Message)
    Write-ColoredOutput "Red" "[ERROR] $Message"
}

function Show-Usage {
    Write-Host "Usage: .\build.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Build ImageViewer application" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -BuildType TYPE      Build type: all, wheel, exe, app (default: all)" -ForegroundColor White
    Write-Host "  -Clean                Clean build directories before building" -ForegroundColor White
    Write-Host "  -Verbose              Enable verbose output" -ForegroundColor White
    Write-Host "  -DistDir DIR          Distribution directory (default: dist)" -ForegroundColor White
    Write-Host "  -BuildDir DIR         Build directory (default: build)" -ForegroundColor White
    Write-Host "  -Help                 Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Build types:" -ForegroundColor White
    Write-Host "  all     Build both wheel package and executable" -ForegroundColor White
    Write-Host "  wheel   Build Python wheel package only" -ForegroundColor White
    Write-Host "  exe     Build standalone executable only" -ForegroundColor White
    Write-Host "  app     Build application bundle (Windows Store app)" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\build.ps1                         # Build everything" -ForegroundColor White
    Write-Host "  .\build.ps1 -BuildType exe          # Build executable only" -ForegroundColor White
    Write-Host "  .\build.ps1 -Clean -Verbose         # Clean and build with verbose output" -ForegroundColor White
}

# Show help and exit if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Function to test if command exists
function Test-Command {
    param([string]$Command)
    try {
        $null = Get-Command $Command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Function to clean build directories
function Clear-BuildDirectories {
    Write-Info "Cleaning build directories..."
    if (Test-Path $BuildDir) {
        Remove-Item -Recurse -Force $BuildDir
    }
    if (Test-Path $DistDir) {
        Remove-Item -Recurse -Force $DistDir
    }
    Remove-Item "*.spec" -ErrorAction SilentlyContinue
    Remove-Item "*.egg-info" -Recurse -ErrorAction SilentlyContinue
    Write-Success "Build directories cleaned"
}

# Function to build Python wheel
function Build-Wheel {
    Write-Info "Building Python wheel package..."
    if (-not (Test-Command "python")) {
        Write-Error "Python not found in PATH"
        exit 1
    }

    try {
        if (Test-Command "uv") {
            & uv run python -m build --wheel
        } else {
            & python -m build --wheel
        }
        Write-Success "Wheel package built successfully"
    }
    catch {
        Write-Error "Failed to build wheel package: $($_.Exception.Message)"
        exit 1
    }
}

# Function to build executable
function Build-Executable {
    Write-Info "Building standalone executable..."

    if (-not (Test-Command "pyinstaller")) {
        Write-Error "PyInstaller not found. Install with: pip install pyinstaller"
        exit 1
    }

    try {
        $pyinstallerArgs = @(
            "--clean",
            "--workpath", $BuildDir,
            "--distpath", $DistDir,
            "--onefile",
            "--noconsole",
            "--name", "imageviewer",
            "--hidden-import", "PIL._tkinter_finder",
            "main.py"
        )

        if ($Verbose) {
            $pyinstallerArgs += "--debug=all"
        }

        & pyinstaller $pyinstallerArgs

        Write-Success "Executable built successfully: $DistDir\imageviewer.exe"
    }
    catch {
        Write-Error "Failed to build executable: $($_.Exception.Message)"
        exit 1
    }
}

# Function to build Windows app package (MSIX)
function Build-AppPackage {
    Write-Info "Building Windows app package..."

    if (-not (Test-Path "$DistDir\imageviewer.exe")) {
        Write-Error "Executable not found. Build the executable first with -BuildType exe"
        exit 1
    }

    Write-Warning "Windows app package building requires additional tools and configuration"
    Write-Info "For now, the executable in $DistDir can be distributed as-is"
    Write-Info "To create a proper Windows app package, consider using:"
    Write-Info "  - Windows Application Packaging Project in Visual Studio"
    Write-Info "  - MSIX Packaging Tool"
    Write-Info "  - Advanced Installer or similar tools"
}

# Main build function
function Invoke-MainBuild {
    Write-Info "Starting ImageViewer build process..."
    Write-Info "Build type: $BuildType"

    # Check if we're in the right directory
    if (-not (Test-Path "pyproject.toml")) {
        Write-Error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    }

    # Clean if requested
    if ($Clean) {
        Clear-BuildDirectories
    }

    # Ensure dist directory exists
    if (-not (Test-Path $DistDir)) {
        New-Item -ItemType Directory -Path $DistDir | Out-Null
    }

    switch ($BuildType) {
        "wheel" {
            Build-Wheel
        }
        "exe" {
            Build-Executable
        }
        "app" {
            Build-AppPackage
        }
        "all" {
            Build-Wheel
            Build-Executable
        }
        default {
            Write-Error "Invalid build type: $BuildType"
            Show-Usage
            exit 1
        }
    }

    Write-Success "Build completed successfully!"
    Write-Info "Output location: $DistDir\"
}

# Run main function
try {
    Invoke-MainBuild
}
catch {
    Write-Error "Build failed: $($_.Exception.Message)"
    exit 1
}
