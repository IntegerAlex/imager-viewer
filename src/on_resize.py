"""Window resize handling logic."""


def on_resize(viewer, event):
    """Handle window resize events by redrawing the image."""
    if event.widget == viewer.root:
        # Redisplay image with current zoom level
        viewer.display_image()

