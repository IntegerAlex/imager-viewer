"""Cursor tracking and pixel color lookup for the debug panel."""

import logging

logger = logging.getLogger(__name__)


def update_cursor_info(viewer, event):
    """Update cursor position and color hex in debug panel."""
    # Store cursor position
    viewer.cursor_pos = (event.x, event.y)
    viewer.cursor_label.config(text=f"Cursor: ({event.x}, {event.y})")

    # Update cursor crosshair lines
    _update_cursor_lines(viewer, event.x, event.y)

    # Get image position and size
    img_x, img_y = viewer.image_pos
    img_w, img_h = viewer.image_size

    # Check if cursor is over the image
    if img_w > 0 and img_h > 0 and (img_x <= event.x < img_x + img_w and img_y <= event.y < img_y + img_h):
        # Calculate relative position within the image
        rel_x = event.x - img_x
        rel_y = event.y - img_y

        # Convert to original image coordinates (account for zoom)
        orig_x = int(rel_x / viewer.zoom_level)
        orig_y = int(rel_y / viewer.zoom_level)

        # Ensure coordinates are within bounds
        orig_x = max(0, min(orig_x, viewer.original_size[0] - 1))
        orig_y = max(0, min(orig_y, viewer.original_size[1] - 1))
        logger.debug("Cursor over image: canvas=(%d, %d) -> image=(%d, %d)", 
                     event.x, event.y, orig_x, orig_y)

        # Get pixel color from original image
        try:
            pixel = viewer.original_image.getpixel((orig_x, orig_y))

            # Convert to hex (handle different image modes)
            if isinstance(pixel, int):  # Grayscale
                hex_color = f"#{pixel:02x}{pixel:02x}{pixel:02x}"
            elif len(pixel) >= 3:  # RGB/RGBA
                r, g, b = pixel[:3]
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                hex_color = "#000000"

            logger.debug("Pixel color at (%d, %d): %s (pixel=%s)", orig_x, orig_y, hex_color, pixel)
            viewer.hex_label.config(text=f"Hex: {hex_color}", fg=hex_color)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Error getting pixel color at (%d, %d): %s", orig_x, orig_y, exc)
            viewer.hex_label.config(text=f"Error: {str(exc)}", fg='white')
    else:
        logger.debug("Cursor outside image bounds: canvas=(%d, %d), image_bounds=(%d,%d)-(%d,%d)", 
                     event.x, event.y, img_x, img_y, img_x + img_w, img_y + img_h)
        viewer.hex_label.config(text="Hex: #000000", fg='white')


def _update_cursor_lines(viewer, x, y):
    """Update the cursor crosshair lines (horizontal red, vertical blue)."""
    canvas_width = viewer.canvas.winfo_width() or 800
    canvas_height = viewer.canvas.winfo_height() or 600
    
    # Delete existing lines
    if hasattr(viewer, 'cursor_h_line') and viewer.cursor_h_line is not None:
        try:
            viewer.canvas.delete(viewer.cursor_h_line)
        except Exception:  # pylint: disable=broad-except
            pass
    
    if hasattr(viewer, 'cursor_v_line') and viewer.cursor_v_line is not None:
        try:
            viewer.canvas.delete(viewer.cursor_v_line)
        except Exception:  # pylint: disable=broad-except
            pass
    
    # Draw horizontal line (red) - full width
    viewer.cursor_h_line = viewer.canvas.create_line(
        0, y, canvas_width, y,
        fill='red',
        dash=(5, 5),  # Dashed pattern: 5px dash, 5px gap
        width=1,
        tags='cursor_line'
    )
    
    # Draw vertical line (blue) - full height
    viewer.cursor_v_line = viewer.canvas.create_line(
        x, 0, x, canvas_height,
        fill='blue',
        dash=(5, 5),  # Dashed pattern: 5px dash, 5px gap
        width=1,
        tags='cursor_line'
    )
    
    # Move lines to top of drawing order (above image)
    viewer.canvas.tag_raise('cursor_line')
    
    logger.debug("Cursor lines updated at (%d, %d)", x, y)


def redraw_cursor_lines(viewer):
    """Redraw cursor lines at current cursor position if available."""
    if hasattr(viewer, 'cursor_pos') and viewer.cursor_pos:
        _update_cursor_lines(viewer, viewer.cursor_pos[0], viewer.cursor_pos[1])

