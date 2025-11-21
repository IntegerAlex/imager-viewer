# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import io
import logging
import os
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageTk

from src.calculate_max_zoom import calculate_max_zoom as calc_max_zoom
from src.display_image import display_image as display_image_fn
from src.handle_zoom import handle_zoom as handle_zoom_fn
from src.handle_pan import handle_pan_start, handle_pan_drag, handle_pan_end
from src.zoom_in import zoom_in as zoom_in_fn
from src.zoom_out import zoom_out as zoom_out_fn
from src.image_metadata import build_metadata_text
from src.on_resize import on_resize as on_resize_fn
from src.services.gemini_image_service import (
    GeminiServiceError,
    generate_image_edit,
)
from src.update_cursor_info import update_cursor_info as update_cursor_info_fn

logger = logging.getLogger(__name__)


class SimpleImageViewer:
    def __init__(self, root, image_path=None, debug_enabled=False, logger_instance=None):
        self.root = root
        self.root.title("advance-image-viewer")
        self.root.geometry("1000x600")
        self.logger = logger_instance or logging.getLogger(self.__class__.__name__)
        self.debug_enabled = debug_enabled

        # Create menu bar
        self.create_menu_bar()

        # Initialize image-related attributes
        self.original_image = None
        self.original_size = None
        self.image_path = None

        # Define zoom constraints - will be updated when image is loaded
        self.min_zoom = 1.0
        self.max_zoom = 1.0  # Default, will be updated when image loads
        self.zoom_level = self.min_zoom  # Start at minimum zoom (1.0x)

        # Main frame to hold canvas and debug panel
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas setup with Windows quality improvements
        canvas_config = {
            'bg': 'gray20',
            'highlightthickness': 0,
        }
        if sys.platform == 'win32':
            # Windows-specific canvas optimizations
            canvas_config.update({
                'borderwidth': 0,
                'relief': tk.FLAT,
            })
        self.canvas = tk.Canvas(main_frame, **canvas_config)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Debug panel frame
        debug_frame = tk.Frame(main_frame, width=200, bg='gray15', padx=10, pady=10)
        debug_frame.pack(side=tk.RIGHT, fill=tk.Y)
        debug_frame.pack_propagate(False)

        # Top control inputs (placeholders for future functionality)
        controls_frame = tk.Frame(debug_frame, bg='gray15')
        controls_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(controls_frame, text="API KEY", bg='gray15', fg='white').pack(anchor=tk.W)
        self.api_key_entry = tk.Entry(controls_frame, bg='gray5', fg='white', insertbackground='white', relief=tk.FLAT, show="•")
        self.api_key_entry.pack(fill=tk.X, pady=(2, 6))
        # Check for GOSS_GEMINI_API_KEY first, fallback to GEMINI_API_KEY for backward compatibility
        env_key = os.environ.get("GOSS_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if env_key:
            self.api_key_entry.insert(0, env_key)
            self._log_debug("API key auto-filled from environment variable")

        tk.Label(controls_frame, text="PROMPT", bg='gray15', fg='white').pack(anchor=tk.W)
        self.prompt_entry = tk.Entry(controls_frame, bg='gray5', fg='white', insertbackground='white', relief=tk.FLAT)
        self.prompt_entry.pack(fill=tk.X, pady=(2, 6))

        self.action_button = tk.Button(
            controls_frame,
            text="Generate",
            relief=tk.FLAT,
            bg='gray30',
            fg='white',
            command=self.handle_generate_click,
        )
        self.action_button.pack(fill=tk.X, pady=(4, 4))

        self.save_button = tk.Button(
            controls_frame,
            text="Save Image",
            relief=tk.FLAT,
            bg='gray30',
            fg='white',
            command=self.handle_save_click,
        )
        self.save_button.pack(fill=tk.X, pady=(4, 0))

        self.status_var = tk.StringVar(value="Awaiting prompt…")
        self.status_label = tk.Label(
            controls_frame,
            textvariable=self.status_var,
            bg='gray15',
            fg='lightgray'
        )
        self.status_label.pack(anchor=tk.W)

        # Debug labels
        tk.Label(debug_frame, text="DEBUG INFO", bg='gray15', fg='white').pack(pady=(0, 10))

        self.cursor_label = tk.Label(debug_frame, text="Cursor: (0, 0)", bg='gray15', fg='white')
        self.cursor_label.pack(anchor=tk.W, pady=2)

        self.hex_label = tk.Label(debug_frame, text="Hex: #000000", bg='gray15', fg='white')
        self.hex_label.pack(anchor=tk.W, pady=2)

        # Now self.min_zoom is defined, so this works
        self.zoom_label = tk.Label(debug_frame, text=f"Zoom: {self.zoom_level:.1f}x", bg='gray15', fg='white')
        self.zoom_label.pack(anchor=tk.W, pady=2)

        # Image metadata (bottom of panel)
        metadata_frame = tk.Frame(debug_frame, bg='gray13', padx=5, pady=5)
        metadata_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        tk.Label(metadata_frame, text="IMAGE METADATA", bg='gray13', fg='white').pack(anchor=tk.W, pady=(0, 4))
        self.metadata_text = tk.Text(
            metadata_frame,
            bg='gray10',
            fg='white',
            wrap=tk.WORD,
            height=14,
            relief=tk.FLAT,
            padx=4,
            pady=4,
        )
        self.metadata_text.pack(fill=tk.BOTH, expand=True)
        self.metadata_text.config(state=tk.DISABLED)

        # Load image if path provided
        if image_path:
            self._log_debug("SimpleImageViewer initializing for %s", image_path)
            self.load_image(image_path)
        else:
            self._log_debug("SimpleImageViewer initializing without image - will show selection dialog")
        self._log_debug("Zoom constraints -> min: %.2f, max: %.2f", self.min_zoom, self.max_zoom)

        # Current cursor position and image position
        self.cursor_pos = (0, 0)
        self.image_pos = (0, 0)
        self.image_size = (0, 0)

        # Panning state
        self.is_panning = False
        self.pan_start_pos = None
        self.pan_start_image_pos = None

        # Cursor crosshair lines
        self.cursor_h_line = None  # Horizontal line ID
        self.cursor_v_line = None  # Vertical line ID
        
        # Bind events
        self.canvas.bind("<MouseWheel>", self.handle_zoom)
        self.root.bind("<Control-plus>", self.zoom_in)
        self.root.bind("<Control-minus>", self.zoom_out)
        self.root.bind("<Control-equal>", self.zoom_in)
        self.canvas.bind("<Motion>", self.update_cursor_info)
        self.root.bind("<Configure>", self.on_resize)
        self.root.bind("<Escape>", lambda e: root.destroy())
        
        # Panning events (left mouse button drag)
        self.canvas.bind("<Button-1>", self.handle_pan_start)
        self.canvas.bind("<B1-Motion>", self.handle_pan_drag)
        self.canvas.bind("<ButtonRelease-1>", self.handle_pan_end)

    def handle_generate_click(self):
        api_key = self.api_key_entry.get().strip()
        prompt = self.prompt_entry.get().strip()

        self._log_debug("Generate clicked. prompt_len=%s, key_provided=%s", len(prompt), bool(api_key))
        if not api_key or not prompt:
            self._set_status("API key and prompt are required.", error=True)
            return

        self.action_button.config(state=tk.DISABLED, text="Generating…")
        self._set_status("Contacting Gemini…")
        worker = threading.Thread(
            target=self._run_generation,
            args=(api_key, prompt),
            daemon=True,
        )
        worker.start()

    def show_image_selection_dialog(self):
        """Show dialog to select an image file from system."""
        file_path = filedialog.askopenfilename(
            title="Select Image File",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.tif"),
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("JPEG files", "*.jpeg"),
                ("GIF files", "*.gif"),
                ("BMP files", "*.bmp"),
                ("TIFF files", "*.tiff"),
                ("TIFF files", "*.tif"),
                ("All files", "*.*"),
            ],
        )
        return file_path

    def create_menu_bar(self):
        """Create the menu bar with File menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open...", command=self.handle_open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save As...", command=self.handle_save_click, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")

        # Bind keyboard shortcuts
        self.root.bind("<Control-o>", lambda e: self.handle_open_file())
        self.root.bind("<Control-O>", lambda e: self.handle_open_file())
        self.root.bind("<Control-s>", lambda e: self.handle_save_click())
        self.root.bind("<Control-S>", lambda e: self.handle_save_click())
        self.root.bind("<Control-q>", lambda e: self.root.quit())
        self.root.bind("<Control-Q>", lambda e: self.root.quit())

    def handle_open_file(self):
        """Handle File -> Open menu action."""
        try:
            file_path = self.show_image_selection_dialog()
            if file_path:
                try:
                    self.load_image(file_path)
                    self._set_status(f"Opened: {os.path.basename(file_path)}", error=False)
                except Exception as e:
                    error_msg = f"Failed to open image: {e}"
                    self._set_status(error_msg, error=True)
                    self._log_debug("Open failed: %s", e)
            else:
                self._log_debug("Open cancelled by user")
        except Exception as exc:
            error_msg = f"Failed to open file dialog: {exc}"
            self._set_status(error_msg, error=True)
            self._log_debug("Open dialog failed: %s", exc)

    def load_image(self, image_path):
        """Load an image and initialize viewer state."""
        try:
            self.original_image = Image.open(image_path)
            self.original_size = self.original_image.size
            self.image_path = os.path.abspath(image_path)
            self._log_debug("Loaded image %s (%s)", image_path, self.original_size)

            # Update zoom constraints now that we have an image
            self.max_zoom = self.calculate_max_zoom()
            self.zoom_level = self.min_zoom

            # Update UI components that depend on having an image
            self.update_metadata_panel()
            self.display_image()

        except Exception as e:
            error_msg = f"Error loading image: {e}"
            print(error_msg)
            self._log_debug("Failed to load image: %s", e)
            # Show error in status if UI is initialized
            if hasattr(self, 'status_var'):
                self._set_status(error_msg, error=True)
            raise

    def handle_save_click(self):
        """Handle save button click - open file dialog and save image."""
        try:
            # Get the original filename to suggest as default
            default_filename = os.path.basename(self.image_path)
            default_name, default_ext = os.path.splitext(default_filename)
            if not default_ext:
                default_ext = ".png"

            # Open file save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Image As",
                defaultextension=default_ext,
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("JPEG files", "*.jpeg"),
                    ("All files", "*.*"),
                ],
                initialfile=default_filename,
            )

            if file_path:
                # Save the original image (not the zoomed/resized version)
                self.original_image.save(file_path)
                self._set_status(f"Image saved to: {os.path.basename(file_path)}", error=False)
                self._log_debug("Image saved to: %s", file_path)
            else:
                self._log_debug("Save cancelled by user")
        except Exception as exc:  # pylint: disable=broad-except
            error_msg = f"Failed to save image: {exc}"
            self._set_status(error_msg, error=True)
            self._log_debug("Save failed: %s", exc)

    def _run_generation(self, api_key, prompt):
        self._log_debug("Gemini generation started on worker thread.")
        try:
            image_bytes = generate_image_edit(api_key, prompt, self.image_path)
        except (ValueError, GeminiServiceError, OSError) as exc:
            self._log_debug("Gemini generation failed: %s", exc)
            error_msg = str(exc)
            # Check if it's a rate limit error
            if "rate limit" in error_msg.lower() or "429" in error_msg or "retry budget" in error_msg.lower():
                error_msg = "Rate limited. Please wait a few minutes and try again."
            self.root.after(0, lambda: self._generation_failed(error_msg))
            return
        except Exception as exc:  # pylint: disable=broad-except
            self._log_debug("Unexpected Gemini generation error: %s", exc)
            error_msg = str(exc)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                error_msg = "Rate limited. Please wait a few minutes and try again."
            self.root.after(0, lambda: self._generation_failed(f"Unexpected error: {error_msg}"))
            return

        self.root.after(0, lambda: self._generation_succeeded(image_bytes))

    def _generation_failed(self, message):
        self.action_button.config(state=tk.NORMAL, text="Generate")
        self._set_status(message, error=True)

    def _generation_succeeded(self, image_bytes):
        try:
            new_image = Image.open(io.BytesIO(image_bytes))
            new_image.load()
            self._log_debug("Generated image loaded (%s)", new_image.size)
        except Exception as exc:  # pylint: disable=broad-except
            self._generation_failed(f"Failed to load generated image: {exc}")
            return

        new_path = self._persist_generated_image(image_bytes)
        self.original_image = new_image
        self.original_size = new_image.size
        self.image_path = new_path
        self.max_zoom = self.calculate_max_zoom()
        self.zoom_level = self.min_zoom
        self.display_image()
        self.update_metadata_panel()

        self.action_button.config(state=tk.NORMAL, text="Generate")
        self._set_status("Image updated.", error=False)

    def _persist_generated_image(self, image_bytes):
        tmp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".png",
            prefix="imageviewer_gemini_",
        )
        with tmp_file:
            tmp_file.write(image_bytes)
        self._log_debug("Generated image persisted to %s", tmp_file.name)
        return tmp_file.name

    def _set_status(self, message, error=False):
        color = 'tomato' if error else 'lightgray'
        self.status_var.set(message)
        if hasattr(self, "status_label"):
            self.status_label.config(fg=color)
        self._log_debug("Status update -> %s", message)
    
    def calculate_max_zoom(self):
        """Calculate max zoom to not exceed 4K resolution"""
        return calc_max_zoom(self.original_size)
    
    def display_image(self, zoom_center=None):
        """Display image at current zoom level with optional zoom center"""
        return display_image_fn(self, zoom_center=zoom_center)
    
    def handle_zoom(self, event):
        """Handle mouse wheel zoom with cursor focus"""
        return handle_zoom_fn(self, event)
    
    def zoom_in(self, event=None):
        """Zoom in with keyboard shortcut (centered on current cursor)"""
        return zoom_in_fn(self, event)
    
    def zoom_out(self, event=None):
        """Zoom out with keyboard shortcut (centered on current cursor)"""
        return zoom_out_fn(self, event)
    
    def update_cursor_info(self, event):
        """Update cursor position and color hex in debug panel"""
        return update_cursor_info_fn(self, event)
    
    def on_resize(self, event):
        """Handle window resize"""
        return on_resize_fn(self, event)
    
    def handle_pan_start(self, event):
        """Handle mouse button press to start panning"""
        return handle_pan_start(self, event)
    
    def handle_pan_drag(self, event):
        """Handle mouse drag to pan the image"""
        return handle_pan_drag(self, event)
    
    def handle_pan_end(self, event):
        """Handle mouse button release to end panning"""
        return handle_pan_end(self, event)

    def update_metadata_panel(self):
        """Populate the metadata text widget with extended image details."""
        metadata = build_metadata_text(self.image_path, self.original_image)
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete("1.0", tk.END)
        self.metadata_text.insert(tk.END, metadata)
        self.metadata_text.config(state=tk.DISABLED)
        self._log_debug("Metadata panel refreshed for %s", self.image_path)

    def _log_debug(self, message, *args):
        if self.debug_enabled:
            self.logger.debug(message, *args)

def parse_cli_args():
    parser = argparse.ArgumentParser(description="An opiniated imageviewer (its a viewer not editor) with AI.")
    parser.add_argument("image_path", nargs="?", help="Path to the image file to open. If not provided, a file selection dialog will open.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    try:
        return parser.parse_args()
    except SystemExit as e:
        # In windowed mode, show error in message box instead of console
        if sys.stdout is None or sys.stderr is None:
            try:
                import tkinter.messagebox as messagebox
                root = tk.Tk()
                root.withdraw()  # Hide main window
                if e.code != 0:  # Error occurred
                    messagebox.showerror(
                        "Command Line Error",
                        "Invalid command line arguments.\n\n"
                        "Usage: imageviewer <image_path> [--debug]\n\n"
                        "Example: imageviewer photo.jpg"
                    )
                root.destroy()
            except Exception:
                pass
        raise


def configure_logging(debug_enabled: bool):
    level = logging.DEBUG if debug_enabled else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def setup_windows_dpi():
    """Configure DPI awareness for Windows to improve rendering quality."""
    if sys.platform == 'win32':
        try:
            # Try to set DPI awareness for better rendering on high-DPI displays
            import ctypes
            # Process DPI awareness
            try:
                # Windows 10 version 1607+
                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
            except (AttributeError, OSError):
                try:
                    # Windows Vista/7/8
                    ctypes.windll.user32.SetProcessDPIAware()
                except (AttributeError, OSError):
                    pass
        except Exception:
            pass  # If DPI setup fails, continue anyway


def main():
    args = parse_cli_args()
    configure_logging(args.debug)
    logger.info("Launching SimpleImageViewer (debug=%s)", args.debug)

    # Check if image path was provided and exists
    if args.image_path and not os.path.exists(args.image_path):
        logger.error("Image not found: %s", args.image_path)
        print(f"Image not found: {args.image_path}")
        sys.exit(1)

    # Setup Windows DPI awareness before creating Tk root
    setup_windows_dpi()

    root = tk.Tk()

    # Windows-specific optimizations
    if sys.platform == 'win32':
        # Improve canvas rendering quality
        try:
            # Set canvas to use better rendering
            root.tk.call('tk', 'scaling', root.tk.call('winfo', 'fpixels', root, '1i') / 96.0)
        except Exception:
            pass

    app = SimpleImageViewer(root, args.image_path, debug_enabled=args.debug, logger_instance=logger)

    root.mainloop()


if __name__ == "__main__":
    # Fix for PyInstaller windowed mode: ensure stdout/stderr are not None
    # When console=False, PyInstaller sets these to None, causing argparse to fail
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    
    try:
        main()
    except SystemExit:
        # Re-raise SystemExit to allow proper exit codes
        raise
    except Exception as e:
        # For windowed mode, show error in a message box if possible
        if sys.stderr is None or sys.stdout is None:
            try:
                import tkinter.messagebox as messagebox
                root = tk.Tk()
                root.withdraw()  # Hide main window
                messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
                root.destroy()
            except Exception:
                pass
        raise
