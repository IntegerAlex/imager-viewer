# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""Keyboard shortcut handler for zooming out."""

import logging

logger = logging.getLogger(__name__)


def zoom_out(viewer, event=None):
    """Zoom out with keyboard shortcut (centered on current cursor)."""
    cursor_x, cursor_y = viewer.cursor_pos
    logger.debug("Zoom out triggered: cursor=(%d, %d), current_zoom=%.2fx", cursor_x, cursor_y, viewer.zoom_level)
    new_zoom = viewer.zoom_level * 0.8
    new_zoom = max(new_zoom, viewer.min_zoom)
    logger.debug("Zoom out: %.2fx -> %.2fx", viewer.zoom_level, new_zoom)

    if abs(new_zoom - viewer.zoom_level) > 0.01:
        viewer.zoom_level = new_zoom
        if viewer.image_size[0] > 0 and viewer.image_size[1] > 0:
            logger.debug("Redisplaying with zoom center at (%d, %d)", cursor_x, cursor_y)
            viewer.display_image(zoom_center=(cursor_x, cursor_y))
        else:
            logger.debug("Redisplaying without zoom center (invalid image size)")
            viewer.display_image()
    else:
        logger.debug("Zoom change too small, skipping redisplay")
    return "break"

