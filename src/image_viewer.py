"""Main image viewer application module."""

import hashlib
import tkinter as tk
from io import BytesIO
from pathlib import Path
from typing import Callable, Optional

from PIL import Image
import PIL._tkinter_finder  # noqa: F401 - Ensure PyInstaller bundles Pillow's Tk bindings

from .image_downloader import download_image_from_url
from .metadata import detect_watermark, format_metadata
from .zoom_helper import ZoomHelper

# UI Constants
TITLE_BAR_BG = "#2D2D2D"
TITLE_BAR_HEIGHT = 28
DEBUG_PANEL_BG = "#2A2A2A"
DEBUG_PANEL_WIDTH = 200
CANVAS_BG = "#1C1C1C"

# macOS Button Colors
BTN_RED = "#FF5F57"
BTN_RED_OUTLINE = "#E0443E"
BTN_YELLOW = "#FFBD2E"
BTN_YELLOW_OUTLINE = "#DEA123"
BTN_GREEN = "#28CA42"
BTN_GREEN_OUTLINE = "#1AAB29"

# Window Constants
INITIAL_GEOMETRY = "1000x700+100+100"
MIN_WINDOW_WIDTH = 400
MIN_WINDOW_HEIGHT = 300
RESIZE_HANDLE_WIDTH = 5
PAN_STEP = 20.0


class ImageViewer:
    """Main image viewer application with macOS-style interface."""
    
    def __init__(self, path: str, is_url: bool = False):
        """Initialize the image viewer."""
        self.root = tk.Tk()
        self.root.title("IMAGE VIEWER")
        self.root.overrideredirect(True)
        self.root.geometry(INITIAL_GEOMETRY)
        
        self._init_state_variables()
        self.original_image = self._load_image(path, is_url)
        self.zoom_helper = ZoomHelper(self.original_image)
        
        self._setup_ui()
        self._bind_events()
        self._initialize_view()
    
    def _init_state_variables(self) -> None:
        """Initialize all state variables."""
        # Window state
        self.is_maximized = False
        self.normal_geometry = None
        
        # Drag state
        self.drag_start_x = self.drag_start_y = 0
        
        # Resize state
        self.resize_start_x = self.resize_start_y = 0
        self.resize_start_width = self.resize_start_height = 0
        self.resize_start_win_x = self.resize_start_win_y = 0
        self.resize_direction = None
        
        # Image metadata
        self.image_url: Optional[str] = None
        self.url_image_size: Optional[int] = None
        self.url_image_hash: Optional[str] = None
        self.resolved_path: Optional[Path] = None
        
        # View state
        self.view_origin_x = self.view_origin_y = 0.0
        self.last_pointer: Optional[tuple[float, float]] = None
        
        # Pan state
        self.is_panning = False
        self.pan_start_x = self.pan_start_y = 0.0
        self.pan_start_view_x = self.pan_start_view_y = 0.0
    
    def _load_image(self, path: str, is_url: bool) -> Image.Image:
        """Load image from file or URL."""
        if is_url:
            return self._load_from_url(path)
        return self._load_from_file(path)
    
    def _load_from_url(self, url: str) -> Image.Image:
        """Load image from URL."""
        print(f"Downloading image from: {url}")
        image_bytes = download_image_from_url(url)
        
        self.url_image_size = len(image_bytes)
        self.url_image_hash = hashlib.md5(image_bytes).hexdigest()
        self.image_url = url
        self.resolved_path = Path(url.split('/')[-1].split('?')[0] or "internet_image")
        
        buffer = BytesIO(image_bytes)
        try:
            with Image.open(buffer) as opened_image:
                opened_image.load()
                return opened_image.copy()
        finally:
            buffer.close()
    
    def _load_from_file(self, path: str) -> Image.Image:
        """Load image from file path."""
        self.resolved_path = Path(path).expanduser().resolve()
        self.image_url = None
        return Image.open(self.resolved_path)
    
    def _setup_ui(self) -> None:
        """Set up all UI components."""
        self._create_title_bar()
        self._create_info_bar()
        self._create_main_container()
        self._create_resize_handles()
    
    def _create_title_bar(self) -> None:
        """Create macOS-style title bar with window controls."""
        title_bar = tk.Frame(self.root, bg=TITLE_BAR_BG, height=TITLE_BAR_HEIGHT)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)
        
        # Window control buttons
        controls = tk.Frame(title_bar, bg=TITLE_BAR_BG)
        controls.pack(side=tk.LEFT, padx=8, pady=6)
        
        self._create_window_button(controls, BTN_RED, BTN_RED_OUTLINE, self._close)
        self._create_window_button(controls, BTN_YELLOW, BTN_YELLOW_OUTLINE, self._minimize)
        self._create_window_button(controls, BTN_GREEN, BTN_GREEN_OUTLINE, self._toggle_maximize)
        
        # Title label
        title = tk.Label(title_bar, text="IMAGE VIEWER", bg=TITLE_BAR_BG, 
                        fg="#CCCCCC", font=("Arial", 10), anchor="center")
        title.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        
        # Make draggable
        for widget in [title_bar, title]:
            widget.bind("<Button-1>", self._start_window_drag)
            widget.bind("<B1-Motion>", self._drag_window)
    
    def _create_window_button(self, parent: tk.Frame, color: str, 
                             outline: str, command: Callable) -> None:
        """Create a macOS-style window control button."""
        btn = tk.Canvas(parent, width=12, height=12, bg=TITLE_BAR_BG, 
                       highlightthickness=0, cursor="hand2")
        btn.pack(side=tk.LEFT, padx=2)
        btn.create_oval(2, 2, 10, 10, fill=color, outline=outline, width=1)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.config(bg="#3D3D3D"))
        btn.bind("<Leave>", lambda e: btn.config(bg=TITLE_BAR_BG))
    
    def _create_info_bar(self) -> None:
        """Create information bar showing zoom and file path."""
        info_frame = tk.Frame(self.root, padx=16, pady=12)
        info_frame.pack(fill=tk.X)
        
        self.zoom_label = tk.Label(info_frame, text="Zoom: 1.0x", font=("Arial", 12))
        self.zoom_label.pack(side=tk.LEFT)
        
        display_path = self.image_url or str(self.resolved_path)
        self.path_label = tk.Label(info_frame, text=display_path, 
                                   font=("Arial", 12), anchor="e")
        self.path_label.pack(side=tk.RIGHT, fill=tk.X, expand=True)
    
    def _create_main_container(self) -> None:
        """Create main container with canvas and debug panel."""
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas
        self.canvas = tk.Canvas(container, background=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create canvas elements
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")
        self.h_line_id = self.canvas.create_line(0, 0, 0, 0, fill="#FF6B6B", 
                                                 width=1, dash=(4, 4), state="hidden")
        self.v_line_id = self.canvas.create_line(0, 0, 0, 0, fill="#4A90E2", 
                                                 width=1, dash=(4, 4), state="hidden")
        self.canvas.tag_raise(self.h_line_id)
        self.canvas.tag_raise(self.v_line_id)
        
        # Debug panel
        self._create_debug_panel(container)
    
    def _create_debug_panel(self, parent: tk.Frame) -> None:
        """Create debug information panel."""
        debug_frame = tk.Frame(parent, width=DEBUG_PANEL_WIDTH, bg=DEBUG_PANEL_BG, 
                              relief=tk.SUNKEN, bd=1)
        debug_frame.pack(side=tk.RIGHT, fill=tk.Y)
        debug_frame.pack_propagate(False)
        
        # Title
        tk.Label(debug_frame, text="Debug Info", font=("Arial", 10, "bold"), 
                bg=DEBUG_PANEL_BG, fg="#FFFFFF").pack(pady=(8, 4))
        
        # Debug labels
        self.cursor_label = self._create_debug_label(debug_frame, "Cursor: --")
        self.zoom_debug_label = self._create_debug_label(debug_frame, "Zoom: --")
        self.view_origin_label = self._create_debug_label(debug_frame, "View: --")
        self.image_size_label = self._create_debug_label(debug_frame, "Image: --")
        self.canvas_size_label = self._create_debug_label(debug_frame, "Canvas: --")
        self.pixel_color_label = self._create_debug_label(debug_frame, "Color: --")
        self.watermark_label = self._create_debug_label(debug_frame, "Watermark: --", 
                                                        fg="#FFD700")
        
        # Metadata section
        tk.Label(debug_frame, text="Metadata", font=("Arial", 10, "bold"), 
                bg=DEBUG_PANEL_BG, fg="#FFFFFF").pack(pady=(12, 4))
        
        metadata_frame = tk.Frame(debug_frame, bg=DEBUG_PANEL_BG)
        metadata_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self.metadata_text = tk.Text(metadata_frame, font=("Courier", 8), 
                                     bg="#1E1E1E", fg="#CCCCCC", wrap=tk.WORD, 
                                     relief=tk.FLAT, padx=4, pady=4, width=22, height=15)
        scrollbar = tk.Scrollbar(metadata_frame, orient=tk.VERTICAL, 
                                command=self.metadata_text.yview)
        self.metadata_text.config(yscrollcommand=scrollbar.set)
        self.metadata_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_debug_label(self, parent: tk.Frame, text: str, fg: str = "#CCCCCC") -> tk.Label:
        """Create a debug info label."""
        label = tk.Label(parent, text=text, font=("Courier", 9), bg=DEBUG_PANEL_BG, 
                        fg=fg, anchor="w", justify="left")
        label.pack(padx=8, pady=2, anchor="w")
        return label
    
    def _create_resize_handles(self) -> None:
        """Create window resize handles."""
        # Bottom edge
        self._create_resize_handle(0, 1, "bottom", "sb_v_double_arrow", "sw",
                                   relwidth=1, height=RESIZE_HANDLE_WIDTH)
        
        # Left edge
        self._create_resize_handle(0, TITLE_BAR_HEIGHT, "left", "sb_h_double_arrow", "nw",
                                   width=RESIZE_HANDLE_WIDTH, relheight=1)
        
        # Right edge
        self._create_resize_handle(1, TITLE_BAR_HEIGHT, "right", "sb_h_double_arrow", "ne",
                                   width=RESIZE_HANDLE_WIDTH, relheight=1)
        
        # Corners
        corner_size = RESIZE_HANDLE_WIDTH * 2
        self._create_resize_handle(0, 1, "bottom-left", "bottom_left_corner", "sw",
                                   width=corner_size, height=corner_size)
        self._create_resize_handle(1, 1, "bottom-right", "bottom_right_corner", "se",
                                   width=corner_size, height=corner_size)
    
    def _create_resize_handle(self, relx: float, rely: float, direction: str, 
                             cursor: str, anchor: str, **kwargs) -> None:
        """Create a single resize handle."""
        handle = tk.Frame(self.root, bg=CANVAS_BG, cursor=cursor)
        place_kwargs = {"relx": relx, "rely": rely, "anchor": anchor, **kwargs}
        handle.place(**place_kwargs)
        handle.bind("<Button-1>", lambda e: self._start_resize(e, direction))
        handle.bind("<B1-Motion>", self._resize_window)
        handle.bind("<ButtonRelease-1>", lambda e: self._stop_resize())
    
    # Window control methods
    def _close(self) -> None:
        """Close the window."""
        self._cleanup()
    
    def _minimize(self) -> None:
        """Minimize the window (withdraw with overrideredirect)."""
        try:
            # Try iconify first (works if overrideredirect is False)
            self.root.iconify()
        except tk.TclError:
            # Fallback: use withdraw which hides the window
            # Note: With overrideredirect, there's no taskbar icon to restore from
            # So this effectively hides the window - user must close it
            # A better solution would be a system tray icon, but that's complex
            self.root.withdraw()
            # Auto-restore after 2 seconds as a workaround
            self.root.after(2000, self.root.deiconify)
    
    def _toggle_maximize(self) -> None:
        """Toggle maximize/restore window."""
        if self.is_maximized:
            if self.normal_geometry:
                self.root.geometry(self.normal_geometry)
            self.is_maximized = False
        else:
            self.normal_geometry = self.root.geometry()
            try:
                self.root.state('zoomed')
            except tk.TclError:
                screen_w = self.root.winfo_screenwidth()
                screen_h = self.root.winfo_screenheight()
                self.root.geometry(f"{screen_w}x{screen_h}+0+0")
            self.is_maximized = True
    
    def _start_window_drag(self, event: tk.Event) -> None:
        """Start window drag."""
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
    
    def _drag_window(self, event: tk.Event) -> None:
        """Handle window dragging."""
        if self.is_maximized:
            self._toggle_maximize()
            self.drag_start_x = event.x_root
            self.drag_start_y = event.y_root
            return
        
        x = self.root.winfo_x() + event.x_root - self.drag_start_x
        y = self.root.winfo_y() + event.y_root - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")
        self.drag_start_x = event.x_root
        self.drag_start_y = event.y_root
    
    def _start_resize(self, event: tk.Event, direction: str) -> None:
        """Start window resize."""
        self.resize_direction = direction
        self.resize_start_x = event.x_root
        self.resize_start_y = event.y_root
        self.resize_start_width = self.root.winfo_width()
        self.resize_start_height = self.root.winfo_height()
        self.resize_start_win_x = self.root.winfo_x()
        self.resize_start_win_y = self.root.winfo_y()
    
    def _resize_window(self, event: tk.Event) -> None:
        """Handle window resizing."""
        if not self.resize_direction:
            return
        
        dx = event.x_root - self.resize_start_x
        dy = event.y_root - self.resize_start_y
        
        new_width = self.resize_start_width
        new_height = self.resize_start_height
        new_x = self.resize_start_win_x
        new_y = self.resize_start_win_y
        
        if "right" in self.resize_direction:
            new_width = max(MIN_WINDOW_WIDTH, self.resize_start_width + dx)
        if "left" in self.resize_direction:
            new_width = max(MIN_WINDOW_WIDTH, self.resize_start_width - dx)
            new_x = self.resize_start_win_x + dx
        if "bottom" in self.resize_direction:
            new_height = max(MIN_WINDOW_HEIGHT, self.resize_start_height + dy)
        if "top" in self.resize_direction:
            new_height = max(MIN_WINDOW_HEIGHT, self.resize_start_height - dy)
            new_y = self.resize_start_win_y + dy
        
        self.root.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
    
    def _stop_resize(self) -> None:
        """Stop window resize."""
        self.resize_direction = None
    
    # Image manipulation methods
    def _clamp(self, value: float, minimum: float, maximum: float) -> float:
        """Clamp value between min and max."""
        return max(minimum, min(value, maximum))
    
    def _get_pixel_color(self, canvas_x: float, canvas_y: float) -> str:
        """Get hex color of pixel at canvas coordinates."""
        try:
            actual_zoom = self.zoom_helper.get_actual_zoom()
            img_x = int((self.view_origin_x + canvas_x) / actual_zoom)
            img_y = int((self.view_origin_y + canvas_y) / actual_zoom)
            
            orig_width, orig_height = self.zoom_helper.get_original_size()
            img_x = self._clamp(img_x, 0, orig_width - 1)
            img_y = self._clamp(img_y, 0, orig_height - 1)
            
            pixel = self.original_image.getpixel((img_x, img_y))
            
            # Handle different pixel formats
            if isinstance(pixel, int):
                r = g = b = pixel
            elif len(pixel) == 3:
                r, g, b = pixel
            elif len(pixel) == 4:
                r, g, b, _ = pixel
            else:
                return "#000000"
            
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return "--"
    
    def _update_metadata(self) -> None:
        """Update metadata display."""
        self.metadata_text.config(state=tk.NORMAL)
        self.metadata_text.delete(1.0, tk.END)
        metadata_str = format_metadata(self.original_image, self.resolved_path, 
                                      self.image_url, self.url_image_size, 
                                      self.url_image_hash)
        self.metadata_text.insert(1.0, metadata_str)
        self.metadata_text.config(state=tk.DISABLED)
    
    def _update_debug_info(self) -> None:
        """Update debug information display."""
        self.canvas.update_idletasks()
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Cursor position
        cursor_text = (f"Cursor: {self.last_pointer[0]:.0f}, {self.last_pointer[1]:.0f}" 
                      if self.last_pointer else "Cursor: --")
        self.cursor_label.config(text=cursor_text)
        
        # Zoom
        zoom_factor = self.zoom_helper.get_zoom_factor()
        self.zoom_debug_label.config(text=f"Zoom: {zoom_factor:.2f}x")
        
        # View origin
        self.view_origin_label.config(text=f"View: {self.view_origin_x:.0f}, {self.view_origin_y:.0f}")
        
        # Image size
        current_photo = getattr(self.canvas, "image", None)
        if current_photo:
            self.image_size_label.config(text=f"Image: {current_photo.width()}x{current_photo.height()}")
        else:
            self.image_size_label.config(text="Image: --")
        
        self.canvas_size_label.config(text=f"Canvas: {canvas_w}x{canvas_h}")
        
        # Pixel color
        if self.last_pointer:
            hex_color = self._get_pixel_color(self.last_pointer[0], self.last_pointer[1])
            self.pixel_color_label.config(text=f"Color: {hex_color}")
        else:
            self.pixel_color_label.config(text="Color: --")
        
        # Watermark
        watermark_info = detect_watermark(self.original_image)
        if len(watermark_info) > 50:
            watermark_info = watermark_info[:47] + "..."
        self.watermark_label.config(text=f"Watermark: {watermark_info}")
    
    def _update_view_position(self) -> None:
        """Update view position and clamp to bounds."""
        self.canvas.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        
        current_photo = getattr(self.canvas, "image", None)
        if current_photo:
            max_origin_x = max(0, current_photo.width() - canvas_w)
            max_origin_y = max(0, current_photo.height() - canvas_h)
            
            self.view_origin_x = self._clamp(self.view_origin_x, 0, max_origin_x)
            self.view_origin_y = self._clamp(self.view_origin_y, 0, max_origin_y)
            
            self.canvas.coords(self.image_id, -self.view_origin_x, -self.view_origin_y)
            self._update_debug_info()
    
    def _render_image(self, photo) -> None:
        """Render PhotoImage on canvas."""
        self.canvas.itemconfigure(self.image_id, image=photo)
        self.canvas.image = photo
        self.canvas.config(scrollregion=(0, 0, photo.width(), photo.height()))
        self._update_view_position()
        self.zoom_label.config(text=f"Zoom: {self.zoom_helper.get_zoom_factor():.2f}x")
        self._update_debug_info()
    
    def _get_focus_point(self) -> tuple[float, float]:
        """Get focus point for zoom (last pointer or canvas center)."""
        if self.last_pointer:
            return self.last_pointer
        self.canvas.update_idletasks()
        return (self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2)
    
    def _apply_zoom(self, zoom_fn: Callable[[], float], 
                   focus: Optional[tuple[float, float]] = None) -> None:
        """Apply zoom change at focus point."""
        focus = focus or self._get_focus_point()
        
        self.canvas.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        
        # Calculate focus point in image coordinates
        current_zoom = self.zoom_helper.get_actual_zoom()
        focus_img_x = (self.view_origin_x + focus[0]) / current_zoom
        focus_img_y = (self.view_origin_y + focus[1]) / current_zoom
        
        # Apply zoom
        zoom_fn()
        photo = self.zoom_helper.get_photo_image()
        new_zoom = self.zoom_helper.get_actual_zoom()
        
        # Update view origin to keep focus point stable
        max_origin_x = max(0, photo.width() - canvas_w)
        max_origin_y = max(0, photo.height() - canvas_h)
        
        self.view_origin_x = self._clamp(focus_img_x * new_zoom - focus[0], 0, max_origin_x)
        self.view_origin_y = self._clamp(focus_img_y * new_zoom - focus[1], 0, max_origin_y)
        
        self._render_image(photo)
    
    def _reset_zoom(self) -> None:
        """Reset zoom to base level."""
        self.zoom_helper.reset_zoom()
        self.view_origin_x = self.view_origin_y = 0.0
        self._render_image(self.zoom_helper.get_photo_image())
    
    def _update_crosshair(self, x: float, y: float) -> None:
        """Update crosshair lines at cursor position."""
        self.canvas.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        
        self.canvas.coords(self.h_line_id, 0, y, canvas_w, y)
        self.canvas.coords(self.v_line_id, x, 0, x, canvas_h)
        self.canvas.itemconfigure(self.h_line_id, state="normal")
        self.canvas.itemconfigure(self.v_line_id, state="normal")
    
    def _hide_crosshair(self) -> None:
        """Hide crosshair lines."""
        self.canvas.itemconfigure(self.h_line_id, state="hidden")
        self.canvas.itemconfigure(self.v_line_id, state="hidden")
    
    def _pan_image(self, dx: float, dy: float) -> None:
        """Pan image by delta."""
        self.view_origin_x += dx
        self.view_origin_y += dy
        self._update_view_position()
    
    # Event handlers
    def _on_mouse_move(self, event: tk.Event) -> None:
        """Handle mouse movement."""
        self.last_pointer = (event.x, event.y)
        
        if self.is_panning:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.view_origin_x = self.pan_start_view_x - dx
            self.view_origin_y = self.pan_start_view_y - dy
            self._update_view_position()
        else:
            self._update_crosshair(event.x, event.y)
            self._update_debug_info()
    
    def _on_mouse_press(self, event: tk.Event) -> None:
        """Handle mouse button press."""
        if event.num in (1, 2):  # Left or middle button
            self.is_panning = True
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.pan_start_view_x = self.view_origin_x
            self.pan_start_view_y = self.view_origin_y
            self.canvas.config(cursor="hand2")
    
    def _on_mouse_release(self, event: tk.Event) -> None:
        """Handle mouse button release."""
        if self.is_panning:
            self.is_panning = False
            self.canvas.config(cursor="")
            self._update_view_position()
    
    def _on_mouse_leave(self, _: tk.Event) -> None:
        """Handle mouse leaving canvas."""
        self.last_pointer = None
        self._hide_crosshair()
        self._update_debug_info()
    
    def _on_mouse_wheel(self, event: tk.Event) -> str:
        """Handle mouse wheel zoom."""
        focus = (event.x, event.y)
        zoom_in = getattr(event, "delta", 0) > 0 or getattr(event, "num", None) == 4
        zoom_fn = self.zoom_helper.zoom_in if zoom_in else self.zoom_helper.zoom_out
        self._apply_zoom(zoom_fn, focus)
        return "break"
    
    def _on_arrow_key(self, event: tk.Event) -> str:
        """Handle arrow key panning."""
        directions = {"Up": (0, -PAN_STEP), "Down": (0, PAN_STEP),
                     "Left": (-PAN_STEP, 0), "Right": (PAN_STEP, 0)}
        dx, dy = directions.get(event.keysym, (0, 0))
        if dx or dy:
            self._pan_image(dx, dy)
        return "break"
    
    def _on_canvas_resize(self, _: tk.Event) -> None:
        """Handle canvas resize."""
        photo = self.zoom_helper.get_photo_image()
        self._render_image(photo)
        if self.last_pointer:
            self._update_crosshair(self.last_pointer[0], self.last_pointer[1])
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        self.zoom_helper.clear_cache()
        try:
            self.original_image.close()
        except Exception:
            pass
        self.root.destroy()
    
    def _bind_events(self) -> None:
        """Bind all event handlers."""
        # Mouse events
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Leave>", self._on_mouse_leave)
        self.canvas.bind("<Button-1>", self._on_mouse_press)
        self.canvas.bind("<Button-2>", self._on_mouse_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.canvas.bind("<ButtonRelease-2>", self._on_mouse_release)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<B2-Motion>", self._on_mouse_move)
        
        # Mouse wheel
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux
        
        # Keyboard zoom
        zoom_in_fn = lambda e: self._apply_zoom(self.zoom_helper.zoom_in, self._get_focus_point())
        zoom_out_fn = lambda e: self._apply_zoom(self.zoom_helper.zoom_out, self._get_focus_point())
        
        for key in ("<plus>", "<equal>", "<KP_Add>"):
            self.root.bind(key, zoom_in_fn)
        for key in ("<minus>", "<KP_Subtract>"):
            self.root.bind(key, zoom_out_fn)
        for key in ("<0>", "<Escape>"):
            self.root.bind(key, lambda e: self._reset_zoom())
        
        # Arrow keys
        for key in ("<Up>", "<Down>", "<Left>", "<Right>"):
            self.root.bind(key, self._on_arrow_key)
        
        # Window events
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._cleanup)
    
    def _initialize_view(self) -> None:
        """Initialize view with proper zoom and render."""
        self.root.update_idletasks()
        canvas_w = max(self.canvas.winfo_width(), 1)
        canvas_h = max(self.canvas.winfo_height(), 1)
        orig_w, orig_h = self.zoom_helper.get_original_size()
        
        if orig_w > 0 and orig_h > 0:
            fit_zoom = min(canvas_w / orig_w, canvas_h / orig_h, 1.0)
            if fit_zoom > 0:
                self.zoom_helper.set_base_zoom(fit_zoom)
        
        self._render_image(self.zoom_helper.get_photo_image())
        self._update_debug_info()
        self._update_metadata()
    
    def run(self) -> None:
        """Start the main event loop."""
        self.root.mainloop()
