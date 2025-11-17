"""Cursor tracking and pixel color lookup for the debug panel."""


def update_cursor_info(viewer, event):
    """Update cursor position and color hex in debug panel."""
    # Store cursor position
    viewer.cursor_pos = (event.x, event.y)
    viewer.cursor_label.config(text=f"Cursor: ({event.x}, {event.y})")

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

            viewer.hex_label.config(text=f"Hex: {hex_color}", fg=hex_color)
        except Exception as exc:  # pylint: disable=broad-except
            viewer.hex_label.config(text=f"Error: {str(exc)}", fg='white')
    else:
        viewer.hex_label.config(text="Hex: #000000", fg='white')

