# ImageViewer Installation Script for Windows
# Copyright (c) 2024 Akshat Kotpalliwar. All rights reserved.

param(
    [ValidateSet("user", "dev", "system")]
    [string]$InstallType = "user",
    [string]$PythonVersion = "",
    [string]$VirtualEnv = ".venv",
    [switch]$Verbose,
    [switch]$Help
)

# Colors for output
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
    Write-Host "Usage: .\install.ps1 [OPTIONS]" -ForegroundColor White
    Write-Host ""
    Write-Host "Install ImageViewer and its dependencies" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor White
    Write-Host "  -InstallType TYPE      Installation type: user, dev, system (default: user)" -ForegroundColor White
    Write-Host "  -PythonVersion VER     Python version to use (default: auto-detect)" -ForegroundColor White
    Write-Host "  -VirtualEnv NAME       Virtual environment name (default: .venv)" -ForegroundColor White
    Write-Host "  -Verbose               Enable verbose output" -ForegroundColor White
    Write-Host "  -Help                  Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Installation types:" -ForegroundColor White
    Write-Host "  user     Install for current user with virtual environment" -ForegroundColor White
    Write-Host "  dev      Install development dependencies" -ForegroundColor White
    Write-Host "  system   Install system-wide" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\install.ps1                         # User install with virtual environment" -ForegroundColor White
    Write-Host "  .\install.ps1 -InstallType dev        # Development install" -ForegroundColor White
    Write-Host "  .\install.ps1 -PythonVersion 3.12     # Use specific Python version" -ForegroundColor White
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

# Function to get Python executable
function Get-PythonExecutable {
    if ($PythonVersion) {
        $pythonCmd = "python$PythonVersion"
        if (Test-Command $pythonCmd) {
            return $pythonCmd
        } else {
            Write-Error "Python $PythonVersion not found"
            exit 1
        }
    } else {
        # Try different Python versions in order of preference
        $pythonVersions = @("python3.12", "python3.11", "python3.10", "python3.9", "python3.8", "python")
        foreach ($py in $pythonVersions) {
            if (Test-Command $py) {
                return $py
            }
        }
        Write-Error "No suitable Python version found"
        exit 1
    }
}

# Function to check system dependencies
function Test-SystemDependencies {
    Write-Info "Checking system dependencies..."

    $missingDeps = @()
    $commands = @("curl", "wget")

    foreach ($cmd in $commands) {
        if (-not (Test-Command $cmd)) {
            $missingDeps += $cmd
        }
    }

    if ($missingDeps.Count -gt 0) {
        Write-Warning "Missing system dependencies: $($missingDeps -join ', ')"
        Write-Info "Please install them using:"
        Write-Info "  - Chocolatey: choco install $($missingDeps -join ' ')"
        Write-Info "  - Scoop: scoop install $($missingDeps -join ' ')"
        Write-Info "  - Or download from their respective websites"
    }
}

# Function to install with uv (modern Python package manager)
function Install-WithUv {
    param([string]$PythonExe)

    Write-Info "Installing with uv..."

    if (-not (Test-Command "uv")) {
        Write-Info "Installing uv package manager..."
        try {
            # Install uv using the official installer
            Invoke-WebRequest -Uri "https://astral.sh/uv/install.ps1" -OutFile "install-uv.ps1"
            & ".\install-uv.ps1"
            Remove-Item "install-uv.ps1"
            # Refresh PATH
            $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        }
        catch {
            Write-Error "Failed to install uv: $($_.Exception.Message)"
            Write-Info "Falling back to pip installation..."
            Install-WithPip $PythonExe
            return
        }
    }

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path $VirtualEnv)) {
        Write-Info "Creating virtual environment: $VirtualEnv"
        & uv venv $VirtualEnv
    }

    # Activate virtual environment
    & "$VirtualEnv\Scripts\Activate.ps1"

    # Install dependencies
    Write-Info "Installing dependencies..."
    & uv sync

    if ($InstallType -eq "dev") {
        Write-Info "Installing development dependencies..."
        & uv sync --dev
    }

    Write-Success "Dependencies installed successfully"
}

# Function to install with pip
function Install-WithPip {
    param([string]$PythonExe)

    Write-Info "Installing with pip..."

    # Create virtual environment if it doesn't exist
    if (-not (Test-Path $VirtualEnv)) {
        Write-Info "Creating virtual environment: $VirtualEnv"
        & $PythonExe -m venv $VirtualEnv
    }

    # Activate virtual environment
    & "$VirtualEnv\Scripts\Activate.ps1"

    # Upgrade pip
    Write-Info "Upgrading pip..."
    & python -m pip install --upgrade pip

    # Install dependencies
    Write-Info "Installing dependencies..."
    if ($InstallType -eq "dev") {
        & pip install -e ".[dev]"
    } else {
        & pip install -e .
    }

    Write-Success "Dependencies installed successfully"
}

# Function to install system-wide
function Install-SystemWide {
    Write-Info "Installing system-wide..."

    if ($InstallType -eq "dev") {
        & pip install -e ".[dev]"
    } else {
        & pip install .
    }

    Write-Success "System-wide installation completed"
}

# Function to verify installation
function Test-Installation {
    Write-Info "Verifying installation..."

    # Activate virtual environment if it exists
    if (Test-Path "$VirtualEnv\Scripts\Activate.ps1") {
        & "$VirtualEnv\Scripts\Activate.ps1"
    }

    # Test import
    try {
        & python -c "from src.image_viewer import ImageViewer; print('ImageViewer import successful')"
        Write-Success "Installation verified successfully"
    }
    catch {
        Write-Error "Installation verification failed: $($_.Exception.Message)"
        exit 1
    }
}

# Function to show post-installation instructions
function Show-PostInstallInstructions {
    Write-Host ""
    Write-Info "Post-installation setup:"
    Write-Host ""
    Write-Host "To activate the virtual environment:" -ForegroundColor White
    Write-Host "  & $VirtualEnv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "To run ImageViewer:" -ForegroundColor White
    Write-Host "  python main.py <image_path>" -ForegroundColor White
    Write-Host "  python main.py --internet <image_url>" -ForegroundColor White
    Write-Host ""
    Write-Host "To build the application:" -ForegroundColor White
    Write-Host "  .\build.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "To deactivate the virtual environment:" -ForegroundColor White
    Write-Host "  deactivate" -ForegroundColor White
}

# Main installation function
function Invoke-MainInstallation {
    Write-Info "Starting ImageViewer installation..."
    Write-Info "Installation type: $InstallType"

    # Check if we're in the right directory
    if (-not (Test-Path "pyproject.toml")) {
        Write-Error "pyproject.toml not found. Please run this script from the project root."
        exit 1
    }

    # Check system dependencies
    Test-SystemDependencies

    # Get Python executable
    $PythonExe = Get-PythonExecutable
    Write-Info "Using Python: $PythonExe"

    switch ($InstallType) {
        "user" {
            # Try uv first, fall back to pip
            if (Test-Command "uv" -or (Test-Command "curl")) {
                try {
                    Install-WithUv $PythonExe
                }
                catch {
                    Write-Warning "uv installation failed, falling back to pip..."
                    Install-WithPip $PythonExe
                }
            } else {
                Install-WithPip $PythonExe
            }
        }
        "dev" {
            # Always try uv for development to ensure all dev dependencies
            try {
                Install-WithUv $PythonExe
            }
            catch {
                Write-Warning "uv installation failed, falling back to pip..."
                Install-WithPip $PythonExe
            }
        }
        "system" {
            Install-SystemWide
        }
        default {
            Write-Error "Invalid installation type: $InstallType"
            Show-Usage
            exit 1
        }
    }

    # Verify installation
    Test-Installation

    Write-Success "ImageViewer installation completed successfully!"
    Show-PostInstallInstructions
}

# Run main function
try {
    Invoke-MainInstallation
}
catch {
    Write-Error "Installation failed: $($_.Exception.Message)"
    exit 1
}
