# Image Viewer

A simple, memory-efficient image viewer with cursor-focused zoom.

## Installation

```bash
uv sync
```

## Usage

### Local Files
```bash
python3 main.py bg.png
# or
python3 main.py --path bg.png
```

### Internet Images
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

## Build Binary

```bash
pyinstaller --clean --workpath build --distpath dist --onefile --noconsole --name imageviewer --hidden-import PIL._tkinter_finder main.py
```

