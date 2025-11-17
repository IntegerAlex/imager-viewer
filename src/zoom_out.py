"""Keyboard shortcut handler for zooming out."""


def zoom_out(viewer, event=None):
    """Zoom out with keyboard shortcut (centered on current cursor)."""
    cursor_x, cursor_y = viewer.cursor_pos
    new_zoom = viewer.zoom_level * 0.8
    new_zoom = max(new_zoom, viewer.min_zoom)

    if abs(new_zoom - viewer.zoom_level) > 0.01:
        viewer.zoom_level = new_zoom
        if viewer.image_size[0] > 0 and viewer.image_size[1] > 0:
            viewer.display_image(zoom_center=(cursor_x, cursor_y))
        else:
            viewer.display_image()
    return "break"

