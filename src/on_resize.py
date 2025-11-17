# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""Window resize handling logic."""

import logging

logger = logging.getLogger(__name__)


def on_resize(viewer, event):
    """Handle window resize events by redrawing the image."""
    if event.widget == viewer.root:
        logger.debug("Window resize event: width=%d, height=%d", event.width, event.height)
        # Redisplay image with current zoom level
        viewer.display_image()
    else:
        logger.debug("Resize event ignored (not root widget): %s", event.widget)

