# Image Viewer

A simple image viewer with Gemini AI image editing integration.

## Features

- **Image viewing** with cursor-focused zoom
- **AI image editing** via Gemini API
- **Debug mode** for troubleshooting

## Usage

```bash
python main.py <image_path> [--debug]
```

### Controls

- **Mouse wheel**: Zoom in/out at cursor
- **Left mouse drag**: Pan the image (when zoomed in)
- **Ctrl + / -**: Zoom in/out
- **Escape**: Close viewer

### Gemini Image Editing

1. Enter your Gemini API key in the "API KEY" field
2. Enter your prompt in the "PROMPT" field
3. Click "Generate" to edit the image

The API key field accepts:
- Plain keys: `AIza...`
- Full URLs: `https://...?key=AIza...`
- Query strings: `key=AIza...`

## Requirements

- Python 3.8+
- PIL/Pillow
- requests

## Installation

```bash
pip install -r requirements.txt
```

## Debug Mode

Enable verbose logging:

```bash
python main.py <image_path> --debug
```
