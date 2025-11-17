"""Mouse wheel zoom handling for the image viewer."""


def handle_zoom(viewer, event):
    """Handle mouse wheel zoom with cursor focus."""
    # Get cursor position relative to canvas
    cursor_x = viewer.canvas.winfo_pointerx() - viewer.canvas.winfo_rootx()
    cursor_y = viewer.canvas.winfo_pointery() - viewer.canvas.winfo_rooty()

    # Determine zoom direction
    if event.delta > 0:  # Zoom in
        new_zoom = viewer.zoom_level * 1.2
    else:  # Zoom out
        new_zoom = viewer.zoom_level * 0.8

    # Apply constraints
    new_zoom = max(viewer.min_zoom, min(new_zoom, viewer.max_zoom))

    # Only update if zoom changed significantly
    if abs(new_zoom - viewer.zoom_level) > 0.01:
        viewer.zoom_level = new_zoom

        # Only use zoom_center if we have valid image dimensions
        if viewer.image_size[0] > 0 and viewer.image_size[1] > 0:
            viewer.display_image(zoom_center=(cursor_x, cursor_y))
        else:
            viewer.display_image()

