"""Mouse wheel zoom handling for the image viewer."""

import logging

logger = logging.getLogger(__name__)


def handle_zoom(viewer, event):
    """Handle mouse wheel zoom with cursor focus."""
    # Get cursor position relative to canvas
    cursor_x = viewer.canvas.winfo_pointerx() - viewer.canvas.winfo_rootx()
    cursor_y = viewer.canvas.winfo_pointery() - viewer.canvas.winfo_rooty()
    logger.debug("Mouse wheel zoom event: delta=%d, cursor=(%d, %d), current_zoom=%.2fx", 
                 event.delta, cursor_x, cursor_y, viewer.zoom_level)

    # Determine zoom direction
    if event.delta > 0:  # Zoom in
        new_zoom = viewer.zoom_level * 1.2
        direction = "in"
    else:  # Zoom out
        new_zoom = viewer.zoom_level * 0.8
        direction = "out"

    # Apply constraints
    new_zoom = max(viewer.min_zoom, min(new_zoom, viewer.max_zoom))
    logger.debug("Zoom %s: %.2fx -> %.2fx (constrained)", direction, viewer.zoom_level, new_zoom)

    # Only update if zoom changed significantly
    if abs(new_zoom - viewer.zoom_level) > 0.01:
        viewer.zoom_level = new_zoom

        # Only use zoom_center if we have valid image dimensions
        if viewer.image_size[0] > 0 and viewer.image_size[1] > 0:
            logger.debug("Redisplaying with zoom center at (%d, %d)", cursor_x, cursor_y)
            viewer.display_image(zoom_center=(cursor_x, cursor_y))
        else:
            logger.debug("Redisplaying without zoom center (invalid image size)")
            viewer.display_image()
    else:
        logger.debug("Zoom change too small, skipping redisplay")

