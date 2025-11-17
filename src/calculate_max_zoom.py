# SPDX-FileCopyrightText: Copyright (C) 2025 Akshat Kotpalliwar (alias IntegerAlex) <inquiry.akshatkotpalliwar@gmail.com>
# SPDX-License-Identifier: GPL-3.0-only

"""Utilities for computing zoom constraints for the image viewer."""

import logging

logger = logging.getLogger(__name__)


def calculate_max_zoom(original_size):
    """Calculate the maximum zoom level without exceeding 4K resolution."""
    logger.debug("Calculating max zoom for image size: %s", original_size)
    if not original_size or original_size[0] == 0 or original_size[1] == 0:
        logger.debug("Invalid image size, returning default zoom 1.0")
        return 1.0

    max_width, max_height = 3840, 2160
    width_ratio = max_width / original_size[0]
    height_ratio = max_height / original_size[1]
    result = min(width_ratio, height_ratio, 10.0)
    logger.debug("Max zoom calculated: %.2fx (width_ratio=%.2f, height_ratio=%.2f)", result, width_ratio, height_ratio)
    return result

