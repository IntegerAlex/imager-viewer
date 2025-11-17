# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""Rendering logic for displaying the image on the canvas."""

import logging

from PIL import Image, ImageTk

logger = logging.getLogger(__name__)


def display_image(viewer, zoom_center=None):
    """
    Display image at current zoom level with optional zoom center.

    Parameters
    ----------
    viewer: SimpleImageViewer
        Instance containing image/canvas state.
    zoom_center: tuple[int, int] | None
        Canvas coordinates to keep fixed during zoom.
    """
    logger.debug("Displaying image at zoom %.2fx (center=%s)", viewer.zoom_level, zoom_center)
    # Apply constraints
    viewer.zoom_level = max(viewer.min_zoom, min(viewer.zoom_level, viewer.max_zoom))

    # Calculate new size
    new_width = int(viewer.original_size[0] * viewer.zoom_level)
    new_height = int(viewer.original_size[1] * viewer.zoom_level)
    logger.debug("Resized dimensions: %dx%d (original: %s)", new_width, new_height, viewer.original_size)

    # Resize image
    resized = viewer.original_image.resize((new_width, new_height), Image.LANCZOS)
    viewer.photo = ImageTk.PhotoImage(resized)

    # Clear canvas
    viewer.canvas.delete("all")

    # Calculate image position
    canvas_width = viewer.canvas.winfo_width() or 800  # Default if not yet mapped
    canvas_height = viewer.canvas.winfo_height() or 600

    if zoom_center and viewer.image_size[0] > 0 and viewer.image_size[1] > 0:
        # Get current image bounds
        old_x, old_y = viewer.image_pos
        old_w, old_h = viewer.image_size

        # Calculate cursor position relative to current image (0.0 to 1.0)
        if old_w > 0 and old_h > 0:
            rel_x = (zoom_center[0] - old_x) / old_w
            rel_y = (zoom_center[1] - old_y) / old_h
        else:
            rel_x, rel_y = 0.5, 0.5

        # Calculate new position to keep cursor point in same place
        new_x = zoom_center[0] - (rel_x * new_width)
        new_y = zoom_center[1] - (rel_y * new_height)

        # Constrain image so it stays aligned with the canvas bounds when smaller,
        # but allow free movement when larger so zoom focuses under the cursor.
        if new_width <= canvas_width:
            new_x = (canvas_width - new_width) // 2
        else:
            new_x = min(0, max(canvas_width - new_width, int(new_x)))

        if new_height <= canvas_height:
            new_y = (canvas_height - new_height) // 2
        else:
            new_y = min(0, max(canvas_height - new_height, int(new_y)))
    else:
        # Center the image normally
        new_x = max(0, (canvas_width - new_width) // 2)
        new_y = max(0, (canvas_height - new_height) // 2)

    # Draw image
    viewer.canvas.create_image(new_x, new_y, anchor="nw", image=viewer.photo)

    # Store current image position and size
    viewer.image_pos = (new_x, new_y)
    viewer.image_size = (new_width, new_height)
    logger.debug("Image positioned at (%d, %d) with size %dx%d", new_x, new_y, new_width, new_height)

    # Update debug info
    viewer.zoom_label.config(text=f"Zoom: {viewer.zoom_level:.1f}x")
    
    # Redraw cursor lines if cursor position is known
    # This ensures lines persist after image redraw
    try:
        from src.update_cursor_info import redraw_cursor_lines
        redraw_cursor_lines(viewer)
    except Exception:  # pylint: disable=broad-except
        # If import fails or lines can't be drawn, continue silently
        # Lines will be redrawn on next mouse movement
        pass

