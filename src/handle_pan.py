# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""Mouse drag panning handling for the image viewer."""

import logging

logger = logging.getLogger(__name__)


def handle_pan_start(viewer, event):
    """Handle mouse button press to start panning."""
    # Only allow panning if image is larger than canvas (zoomed in)
    canvas_width = viewer.canvas.winfo_width() or 800
    canvas_height = viewer.canvas.winfo_height() or 600
    if viewer.image_size[0] > canvas_width or viewer.image_size[1] > canvas_height:
        viewer.pan_start_pos = (event.x, event.y)
        viewer.pan_start_image_pos = viewer.image_pos
        viewer.is_panning = True
        logger.debug("Pan started at (%d, %d), image_pos=(%d, %d)", 
                     event.x, event.y, viewer.image_pos[0], viewer.image_pos[1])
    else:
        logger.debug("Pan ignored - image fits within canvas")


def handle_pan_drag(viewer, event):
    """Handle mouse drag to pan the image."""
    if not viewer.is_panning:
        return

    # Calculate drag delta
    dx = event.x - viewer.pan_start_pos[0]
    dy = event.y - viewer.pan_start_pos[1]

    # Calculate new image position
    new_x = viewer.pan_start_image_pos[0] + dx
    new_y = viewer.pan_start_image_pos[1] + dy

    # Constrain image position to canvas bounds
    canvas_width = viewer.canvas.winfo_width() or 800
    canvas_height = viewer.canvas.winfo_height() or 600

    # Only constrain if image is larger than canvas
    if viewer.image_size[0] > canvas_width:
        new_x = min(0, max(canvas_width - viewer.image_size[0], new_x))
    else:
        new_x = max(0, (canvas_width - viewer.image_size[0]) // 2)

    if viewer.image_size[1] > canvas_height:
        new_y = min(0, max(canvas_height - viewer.image_size[1], new_y))
    else:
        new_y = max(0, (canvas_height - viewer.image_size[1]) // 2)

    # Update image position
    viewer.image_pos = (int(new_x), int(new_y))
    
    # Redraw image at new position
    viewer.canvas.delete("all")
    viewer.canvas.create_image(viewer.image_pos[0], viewer.image_pos[1], anchor="nw", image=viewer.photo)
    
    logger.debug("Pan drag: delta=(%d, %d), new_image_pos=(%d, %d)", dx, dy, viewer.image_pos[0], viewer.image_pos[1])


def handle_pan_end(viewer, event):
    """Handle mouse button release to end panning."""
    if viewer.is_panning:
        logger.debug("Pan ended at (%d, %d), final_image_pos=(%d, %d)", 
                     event.x, event.y, viewer.image_pos[0], viewer.image_pos[1])
        viewer.is_panning = False
        viewer.pan_start_pos = None
        viewer.pan_start_image_pos = None

