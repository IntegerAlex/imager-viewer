# Contributing to Advance Image Viewer

A comprehensive guide for developers and contributors to the Advance Image Viewer project.

## Development Environment Setup

### Development Dependencies
- **Build System**: PyInstaller for creating standalone executable artifacts
- **Package Management**: pip for dependency resolution and virtual environment management
- **Version Control**: Git for distributed source code management
- **API Testing**: GitHub CLI for release management and repository operations

### Development Environment Setup

#### Repository Setup
```bash
# Clone the repository
git clone https://github.com/IntegerAlex/advance-image-viewer.git
cd advance-image-viewer
```

#### Virtual Environment Configuration
```bash
# Create isolated Python environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows (PowerShell)

# Install runtime dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

#### Development Dependencies
Additional packages for development and testing may include:
- Build tools (PyInstaller, setuptools)
- Testing frameworks (pytest, unittest)
- Code quality tools (flake8, black, mypy)
- Documentation generators (Sphinx)

## Artifact Compilation Pipeline

### PyInstaller Integration
Leverages PyInstaller for generating self-contained executable artifacts with comprehensive dependency bundling and cross-platform compatibility.

**Automated Build Process:**
```bash
# Recommended: Utilize the custom build orchestration script
python build.py
```

**Direct PyInstaller Invocation:**
```bash
# Manual compilation using PyInstaller specification
pyinstaller imageviewer.spec
```

**Output Artifacts:**
- **POSIX Systems**: `dist/imageviewer` (ELF executable)
- **Windows Platform**: `dist/imageviewer.exe` (PE executable)

### Compilation Configuration Options

**Clean Build Environment:**
```bash
# Purge previous compilation artifacts
python build.py --clean
```

**Technical Implementation Details:**
- **Dependency Resolution**: Complete Python runtime and library bundling for standalone execution
- **Single-File Distribution**: Monolithic executable containing all runtime dependencies
- **Cross-Platform Compatibility**: Architecture-specific binary generation with platform detection
- **Resource Optimization**: Intelligent packaging with duplicate elimination and compression algorithms

## Release Engineering Pipeline

### GitHub Release Automation
Sophisticated CI/CD pipeline for automated artifact distribution and version management.

### System Prerequisites

**Authentication Infrastructure:**
- GitHub CLI (`gh`) with OAuth token authentication
- Git remote repository configuration with push permissions
- Semantic versioning compliance in `pyproject.toml`

### Platform-Specific Release Orchestration

#### POSIX-Compatible Execution Environment
```bash
./release.sh
```

#### Windows PowerShell Execution Context
```powershell
.\release.ps1
```

### Operational Workflow

**Automated Release Sequence:**
1. **Artifact Generation**: Platform-specific binary compilation using PyInstaller
2. **Version Control Tagging**: Semantic version tags (`v{major}.{minor}.{patch}`) and rolling `latest` tag
3. **GitHub Release Creation**: Automated release manifest generation with comprehensive changelogs
4. **Asset Distribution**: Multi-architecture binary uploads with integrity verification

### Multi-Platform Distribution Strategy

**Current Implementation:** Execute release scripts on each target platform for native compilation.

**Future Enhancement:** GitHub Actions matrix builds for automated cross-platform artifact generation and unified release management.

**Release Asset Naming Convention:**
- Linux: `imageviewer-linux-{architecture}` (x86_64, aarch64)
- Windows: `imageviewer.exe-windows-{architecture}.exe`
- macOS: `imageviewer-darwin-{architecture}` (planned)

## Diagnostic Instrumentation Framework

### Real-Time Telemetry Interface

![Diagnostic Instrumentation Panel](screenshots/debug.png)

**Performance Monitoring Dashboard:**
- **Coordinate Tracking**: Real-time cursor position mapping with sub-pixel precision
- **Colorimetric Analysis**: Hexadecimal pixel value extraction and RGB decomposition
- **Scale Factor Monitoring**: Dynamic zoom level quantification with transformation matrix visualization
- **Metadata Extraction**: Comprehensive EXIF data parsing and image attribute enumeration

![Metadata Analysis Interface](screenshots/image-metadata.png)

**Image Intelligence Extraction:**
- File format identification and codec information
- Dimensional analysis (resolution, aspect ratio, bit depth)
- Color space characterization and gamma correction data
- Geospatial positioning and temporal metadata
- Compression algorithm detection and quality metrics

### Verbose Execution Mode

**Enhanced Logging Activation:**
```bash
python main.py <image_path> --debug
```

**Instrumentation Capabilities:**
- Event-driven logging with timestamp correlation
- Memory usage profiling and garbage collection statistics
- API call tracing with latency measurement
- Exception handling with stack trace preservation
- Performance bottleneck identification and optimization guidance

## Codebase Architecture

### Project Structure
```
advance-image-viewer/
├── main.py                 # Application entry point
├── build.py               # Build orchestration script
├── imageviewer.spec       # PyInstaller specification
├── pyproject.toml         # Project metadata and dependencies
├── requirements.txt       # Python dependencies
├── src/                   # Source code directory
├── dist/                  # Build artifacts (generated)
├── release/               # Release artifacts (generated)
├── screenshots/           # Documentation images
├── installer.sh           # Linux installation script
├── installer.ps1          # Windows installation script
├── release.sh             # Linux release script
├── release.ps1            # Windows release script
└── cloudflare/            # Cloudflare Worker for CDN distribution
```

### Key Components

**Core Application (`main.py`):**
- GUI initialization and event loop management
- Image loading and rendering pipeline
- AI integration and API communication
- User interaction handling

**Build System (`build.py`):**
- Cross-platform compilation orchestration
- Dependency analysis and bundling
- Platform-specific optimizations

**Cloudflare Integration:**
- Serverless function for global distribution
- Automated installer serving
- CDN caching and performance optimization

## Development Workflow

### 1. Local Development
```bash
# Run in development mode
python main.py path/to/image.jpg

# Run with debug logging
python main.py path/to/image.jpg --debug
```

### 2. Testing Changes
```bash
# Test build process
python build.py --clean
python build.py

# Verify executable creation
ls -la dist/
./dist/imageviewer path/to/test/image.jpg
```

### 3. Release Process
```bash
# Update version in pyproject.toml
# Commit changes
git commit -m "Release v1.2.3"

# Create release (Linux/macOS)
./release.sh

# Create release (Windows)
.\release.ps1
```

## Contributing Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use descriptive variable and function names
- Include docstrings for all public functions
- Maintain type hints where applicable

### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Issue Reporting
- Use GitHub issues for bug reports and feature requests
- Include detailed reproduction steps for bugs
- Attach relevant screenshots or log output
- Specify your platform and Python version

### Documentation
- Update README.md for user-facing changes
- Update this CONTRIBUTING.md for development-related changes
- Include code comments for complex algorithms
- Maintain changelog in release descriptions

## Performance Optimization

### Profiling Techniques
```python
import cProfile
import pstats

# Profile application startup
cProfile.run('main()', 'profile_output.prof')

# Analyze results
p = pstats.Stats('profile_output.prof')
p.sort_stats('cumulative').print_stats(20)
```

### Memory Management
- Use PIL's lazy loading for large images
- Implement proper cleanup of Tkinter widgets
- Monitor memory usage in debug mode
- Optimize image resizing algorithms

### Build Optimization
- Minimize PyInstaller bundle size
- Exclude unnecessary dependencies
- Use UPX compression for executables
- Test builds on target platforms

---

*"Great software is built by great communities. Your contributions make this vision a reality."*
