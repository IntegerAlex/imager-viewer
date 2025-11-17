# Advance Image Viewer

A sophisticated, AI-enhanced image visualization and analysis application built with Python, featuring advanced cursor-based zoom mechanics and seamless integration with Google's Gemini multimodal models for intelligent image manipulation.

![Application Interface](screenshots/application.png)

*"...where computational vision meets artificial intelligence"* - A modern approach to digital image analysis and transformation.

## Core Features

Advance Image Viewer combines traditional image viewing capabilities with cutting-edge AI technology:

- **Advanced Visualization**: Cursor-centric zoom, high-performance rendering, and adaptive pan control
- **AI-Powered Editing**: Direct integration with Google's Gemini models for intelligent image manipulation
- **Developer Tools**: Comprehensive debugging interface and performance profiling

For detailed feature descriptions, see [FEATURES.md](FEATURES.md).

## Technical Architecture

### Core Implementation

Built with Python 3.10+ utilizing the Tkinter GUI framework for cross-platform compatibility and PIL/Pillow for robust image processing operations. The application implements a modular event-driven architecture with separation of concerns between visualization, AI integration, and user interface components.

### Command Line Interface

```bash
python main.py <image_path> [--debug]
```

**Parameters:**

- `<image_path>`: Path to target image file (supports all PIL-compatible formats)
- `--debug`: Enables verbose logging and diagnostic interface

### Human-Computer Interaction Protocol

#### Primary Input Modalities

- **Orbital Navigation**: Mouse wheel implements logarithmic zoom scaling centered on cursor coordinates using advanced transformation matrices
- **Translational Manipulation**: Left mouse button enables viewport translation with momentum-based physics simulation
- **Keyboard Accelerators**: Ctrl + / - provides discrete zoom levels with hysteresis compensation
- **Termination Sequence**: Escape key triggers graceful application shutdown with resource cleanup

#### AI-Enhanced Image Transformation Pipeline

![AI-Generated Content](screenshots/ai-generated.png)

**Operational Workflow:**

1. **Authentication Configuration**: Secure API key provisioning via environment variables or direct input
2. **Semantic Prompt Processing**: Natural language interpretation for precise transformation directives
3. **Neural Network Inference**: Real-time interaction with Gemini multimodal models
4. **Artifact Persistence**: High-fidelity image serialization to filesystem

**Environment Variable Configuration:**

```bash
# Primary configuration
export GOSS_GEMINI_API_KEY="your-api-key-here"

# Fallback compatibility
export GEMINI_API_KEY="your-api-key-here"
```

**Shell Integration (Bash/Zsh):**
```bash
echo 'export GOSS_GEMINI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**API Key Format Flexibility:**

- **Raw Authentication**: Direct API key strings (`AIzaSy...`)
- **URL Encapsulation**: Complete endpoint URLs with embedded credentials
- **Query Parameter Extraction**: Isolated key-value pairs for modular configuration

## System Prerequisites

### Runtime Dependencies

- **Python Ecosystem**: Version 3.8 or higher with comprehensive standard library support
- **Image Processing Library**: PIL/Pillow for advanced bitmap manipulation and format support
- **HTTP Client Library**: Requests for robust REST API communication with connection pooling and SSL verification
- **GUI Framework**: Tkinter (bundled with Python) for cross-platform graphical user interface implementation

## Deployment Strategies

### Binary Distribution (Recommended)

#### POSIX-Compatible Systems (Linux/macOS)

**Cloudflare CDN Distribution:**
```bash
curl -fsSL https://advance-image-viewer.gossorg.in | bash
```

**Manual Installation Protocol:**
```bash
# Ensure executable permissions
chmod +x installer.sh

# Execute deployment script
./installer.sh
```

**Installation Vector Analysis:**

- Automated binary retrieval from GitHub releases
- Strategic placement in `~/.local/bin/` for user-level accessibility
- PATH environment augmentation with conflict detection
- Integrity verification through checksum validation

#### Microsoft Windows Platform

**Primary Installation Vector:**

```powershell
irm https://advance-image-viewer.gossorg.in | iex
```

**Execution Policy Configuration:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm https://advance-image-viewer.gossorg.in | iex
```

**Fallback Distribution Channel:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/IntegerAlex/advance-image-viewer/master/installer.ps1" -OutFile installer.ps1
.\installer.ps1
```

**Windows Deployment Characteristics:**
- Binary artifact retrieval via GitHub API integration
- Installation target: `%LOCALAPPDATA%\Programs\advance-image-viewer\imageviewer.exe`
- Automated PATH registry modification with administrative privilege detection

## Technical Philosophy & Architectural Principles

### Design Philosophy
This project embodies a synthesis of classical computer vision techniques with contemporary artificial intelligence paradigms. The application serves as a bridge between traditional image processing methodologies and the transformative potential of generative AI, creating an accessible interface for computational creativity.

### Core Architectural Tenets

**Modularity & Extensibility:**
- Clean separation of concerns between UI, processing, and AI components
- Plugin architecture for future AI model integrations
- Event-driven design patterns for maintainable codebase evolution

**Performance Optimization:**
- Lazy loading and memory-efficient image handling
- Asynchronous AI processing to maintain responsive UI
- Intelligent caching strategies for repeated operations

**Cross-Platform Compatibility:**
- Native platform integration respecting OS conventions
- Consistent user experience across diverse computing environments
- Minimal dependency footprint for broad accessibility

### Future Research Directions

**Advanced AI Integration:**
- Multi-modal image understanding with contextual reasoning
- Real-time collaborative editing capabilities
- Integration with emerging vision-language models

**Performance Enhancements:**
- GPU acceleration for computationally intensive operations
- Progressive loading for large image datasets
- Advanced compression algorithms for network distribution

**User Experience Innovation:**
- Gesture-based interaction paradigms
- Voice-controlled image manipulation
- Immersive augmented reality visualization modes

## Additional Resources

- **[FEATURES.md](FEATURES.md)**: Comprehensive feature documentation and technical specifications
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development guide for contributors and maintainers
- **[LICENSE](LICENSE)**: GNU General Public License v3.0 terms and conditions
- **[COPYRIGHT](COPYRIGHT)**: Copyright notices and licensing information

---

*"In the convergence of human perception and machine intelligence lies the future of creative computation."*
