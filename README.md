# Image Viewer

A simple, memory-efficient image viewer with cursor-focused zoom.

## Quick Start

### Installation

#### Cross-Platform Installation (Recommended)

For regular users:
```bash
python install.py
```

For developers:
```bash
python dev-setup.sh  # or ./dev-setup.sh on Linux/macOS
```

#### Platform-Specific Installation

**Linux/macOS:**
```bash
./install.sh              # User install
./dev-setup.sh            # Development setup
```

**Windows (PowerShell):**
```powershell
.\install.ps1             # User install
.\dev-setup.ps1           # Development setup (when available)
```

**Windows (Command Prompt):**
```cmd
install.bat               # Simple batch wrapper
python install.py         # Cross-platform wrapper
```

### Remote Installation

For the quickest installation experience, you can install ImageViewer directly from our remote installer:

#### Linux/macOS
```bash
curl -fsSL https://imageviewer-installer.gossorg.in/install.sh | bash
```

#### Windows (PowerShell)
```powershell
irm https://imageviewer-installer.gossorg.in/install.ps1 | iex
```

#### Windows (Command Prompt)
```cmd
curl -fsSL https://imageviewer-installer.gossorg.in/install.ps1 | powershell -ExecutionPolicy Bypass -
```

The remote installer will:
- Download the latest pre-built binary for your platform
- Verify binary integrity with SHA256 checksums
- Install to the appropriate location
- Add to your PATH automatically
- Provide usage instructions

### Usage

#### Activate Virtual Environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
& .venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

#### Local Files
```bash
python3 main.py bg.png
# or
python3 main.py --path bg.png
```

#### Internet Images
```bash
python3 main.py --internet "https://images.unsplash.com/photo-1761839258623-e232e15f7ff3?q=80&w=687"
```

## Controls

### Zoom
- **Mouse wheel**: Zoom in/out at cursor position
- **+ / =**: Zoom in at cursor
- **-**: Zoom out at cursor
- **0 / Escape**: Reset zoom to 1:1

### Panning
- **Left mouse button drag**: Pan the image (drag to move)
- **Middle mouse button drag**: Pan the image
- **Arrow keys**: Pan in small increments (↑ ↓ ← →)

## Development

### Setup Development Environment

```bash
./dev-setup.sh
```

This will:
- Create a virtual environment
- Install all dependencies (including development tools)
- Set up pre-commit hooks
- Run initial checks and tests

### Available Scripts

#### Cross-Platform Scripts (Recommended)

- **`python build.py`** - Cross-platform build script
  - `--type exe` - Build executable only
  - `--type wheel` - Build Python wheel only
  - `--type all` - Build both (default)
  - `--clean` - Clean build directories first
  - `--help-platform` - Show detected platform info

- **`python install.py`** - Cross-platform installation script
  - `--type dev` - Install with development dependencies
  - `--type system` - Install system-wide
  - `--python 3.12` - Use specific Python version
  - `--help-platform` - Show detected platform info

#### Linux/macOS Scripts

- **`./install.sh`** - Install dependencies for regular use
  - `--type dev` - Install with development dependencies
  - `--type system` - Install system-wide
  - `--python 3.12` - Use specific Python version

- **`./dev-setup.sh`** - Complete development environment setup
  - `--python 3.12` - Use specific Python version
  - `--skip-tests` - Skip test execution

- **`./build.sh`** - Build the application
  - `--type exe` - Build executable only
  - `--type wheel` - Build Python wheel only
  - `--type all` - Build both (default)
  - `--clean` - Clean build directories first

- **`./run-tests.sh`** - Run test suite
  - `--type unit` - Run unit tests only
  - `--type integration` - Run integration tests only
  - `--type lint` - Run linting checks only
  - `--type all` - Run all tests (default)
  - `--coverage` - Generate coverage report

#### Windows Scripts

- **`install.bat`** - Simple installation wrapper (Command Prompt)
  - `--type dev` - Install with development dependencies
  - `--type system` - Install system-wide
  - `--python 3.12` - Use specific Python version

- **`build.bat`** - Simple build wrapper (Command Prompt)
  - `--type exe` - Build executable only
  - `--type wheel` - Build Python wheel only
  - `--type all` - Build both (default)
  - `--clean` - Clean build directories first

- **`.\install.ps1`** - Full installation script (PowerShell)
  - `-InstallType dev` - Install with development dependencies
  - `-InstallType system` - Install system-wide
  - `-PythonVersion 3.12` - Use specific Python version

- **`.\build.ps1`** - Full build script (PowerShell)
  - `-BuildType exe` - Build executable only
  - `-BuildType wheel` - Build Python wheel only
  - `-BuildType all` - Build both (default)
  - `-Clean` - Clean build directories first

### Manual Build

#### Python Package
```bash
python -m build --wheel
```

#### Standalone Executable

**Linux/macOS:**
```bash
pyinstaller --clean --workpath build --distpath dist --onefile --noconsole --name imageviewer --hidden-import PIL._tkinter_finder main.py
```

**Windows:**
```powershell
pyinstaller --clean --workpath build --distpath dist --onefile --noconsole --name imageviewer --hidden-import PIL._tkinter_finder main.py
```

## Platform Requirements

### Linux
- Python 3.8+
- bash shell
- curl or wget (for uv installation)

### macOS
- Python 3.8+
- bash shell (Terminal)
- Xcode Command Line Tools (for some dependencies)

### Windows
- Python 3.8+
- PowerShell 5.1+ or Windows Terminal with PowerShell
- Windows 10/11

### Optional Dependencies
- **uv** - Modern Python package manager (recommended)
- **PyInstaller** - For building standalone executables
- **Development tools** - pytest, black, flake8, mypy (for development)

## Deploying Remote Installer

The remote installer is powered by Cloudflare Workers. To deploy it:

1. **Install Wrangler CLI:**
   ```bash
   npm install -g wrangler
   ```

2. **Authenticate with Cloudflare:**
   ```bash
   wrangler auth login
   ```

3. **Configure your domain** in `cloudflare/wrangler.toml`:
   ```toml
   [[routes]]
   pattern = "imageviewer-installer.yourdomain.com/*"
   zone_name = "yourdomain.com"
   ```

4. **Deploy the worker:**
   ```bash
   ./scripts/deploy-worker.sh
   ```

### Local Development

Test the worker locally:
```bash
cd cloudflare
wrangler dev
```

Test the endpoints:
```bash
curl http://localhost:8787/health
curl http://localhost:8787/install.sh
curl http://localhost:8787/install.ps1
```

## Troubleshooting

### Windows
- **PowerShell execution policy**: If you get execution policy errors, run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Python not found**: Ensure Python is in your PATH
- **Virtual environment activation**: Use `& .venv\Scripts\Activate.ps1` in PowerShell

### Linux/macOS
- **Permission denied**: Make scripts executable with `chmod +x script.sh`
- **Python version issues**: Use `--python` flag to specify version
- **Missing dependencies**: Install system packages as prompted by scripts

### General
- **Build fails**: Try `--clean` flag to clean previous builds
- **Import errors**: Ensure virtual environment is activated
- **Network issues**: Check internet connection for dependency downloads

### Testing

Run all tests:
```bash
./run-tests.sh
```

Run with coverage:
```bash
./run-tests.sh --coverage
```

Run specific test types:
```bash
./run-tests.sh --type lint    # Linting only
./run-tests.sh --type unit    # Unit tests only
```

### Code Quality

The project uses pre-commit hooks for code quality. They run automatically on commits, but you can run them manually:

```bash
pre-commit run --all-files
```

