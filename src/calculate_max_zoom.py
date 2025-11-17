"""Utilities for computing zoom constraints for the image viewer."""


def calculate_max_zoom(original_size):
    """Calculate the maximum zoom level without exceeding 4K resolution."""
    if not original_size or original_size[0] == 0 or original_size[1] == 0:
        return 1.0

    max_width, max_height = 3840, 2160
    width_ratio = max_width / original_size[0]
    height_ratio = max_height / original_size[1]
    return min(width_ratio, height_ratio, 10.0)

