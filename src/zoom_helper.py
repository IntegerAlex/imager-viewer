# SPDX-License-Identifier: GPL-3.0-only
# Copyright (c) 2024 Akshat Kotpalliwar <inquiry.akshatkotpalliwar@gmail.com>

"""Helper module for zoom operations in the image viewer."""

import gc
import math
from typing import Optional

from PIL import Image, ImageTk

# Constants
MAX_WIDTH = 3840  # 4K resolution limit
MAX_HEIGHT = 2160
MAX_CACHE_IMAGES = 5
MAX_CACHE_PHOTOS = 3
ZOOM_STEP = 0.1
MIN_ZOOM = 1.0
MAX_ZOOM = 10.0


class ZoomHelper:
    """Manages zoom operations with caching and memory optimization."""
    
    def __init__(self, original_image: Image.Image):
        """Initialize zoom helper with an image."""
        self.original_image = original_image.copy()
        self.base_zoom = 1.0
        self.display_zoom = 1.0
        self.max_actual_zoom = self._calculate_safe_max_zoom()
        
        self._image_cache: dict[float, Image.Image] = {}
        self._photo_cache: dict[float, ImageTk.PhotoImage] = {}
        self._current_photo: Optional[ImageTk.PhotoImage] = None
    
    def _calculate_safe_max_zoom(self) -> float:
        """Calculate safe maximum zoom to prevent memory issues."""
        w, h = self.original_image.size
        max_by_width = MAX_WIDTH / max(w, 1)
        max_by_height = MAX_HEIGHT / max(h, 1)
        return max(1.0, min(max_by_width, max_by_height, MAX_ZOOM))
    
    def set_base_zoom(self, base_zoom: float) -> None:
        """Set base zoom (fit scale) and reset caches."""
        self.base_zoom = max(base_zoom, 1e-6)
        self.display_zoom = 1.0
        self.clear_cache()
    
    def get_actual_zoom(self) -> float:
        """Get actual scaling applied to original image."""
        return self.base_zoom * self.display_zoom
    
    def get_zoom_factor(self) -> float:
        """Get user-facing zoom multiplier."""
        return self.display_zoom
    
    def get_original_size(self) -> tuple[int, int]:
        """Get original image dimensions."""
        return self.original_image.size
    
    def zoom_in(self) -> float:
        """Increase zoom factor."""
        max_display = self.max_actual_zoom / self.base_zoom
        self.display_zoom = min(self.display_zoom + ZOOM_STEP, max_display)
        return self.display_zoom
    
    def zoom_out(self) -> float:
        """Decrease zoom factor (minimum 1.0)."""
        self.display_zoom = max(self.display_zoom - ZOOM_STEP, MIN_ZOOM)
        return self.display_zoom
    
    def reset_zoom(self) -> float:
        """Reset to base zoom."""
        self.display_zoom = 1.0
        return self.display_zoom
    
    def _limit_size(self, width: int, height: int) -> tuple[int, int]:
        """Limit dimensions to prevent memory issues."""
        if width > MAX_WIDTH or height > MAX_HEIGHT:
            ratio = min(MAX_WIDTH / width, MAX_HEIGHT / height)
            return int(width * ratio), int(height * ratio)
        return width, height
    
    def get_zoomed_image(self) -> Image.Image:
        """Get scaled image with caching."""
        actual_zoom = self.get_actual_zoom()
        cache_key = round(actual_zoom, 3)
        
        # Check cache
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]
        
        # Return original if zoom is ~1.0
        if math.isclose(actual_zoom, 1.0, rel_tol=1e-6):
            self._image_cache[cache_key] = self.original_image
            return self.original_image
        
        # Resize image
        w, h = self.original_image.size
        new_w, new_h = self._limit_size(int(w * actual_zoom), int(h * actual_zoom))
        zoomed = self.original_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Cache with size limit
        if len(self._image_cache) >= MAX_CACHE_IMAGES:
            del self._image_cache[min(self._image_cache.keys())]
        
        self._image_cache[cache_key] = zoomed
        return zoomed
    
    def get_photo_image(self) -> ImageTk.PhotoImage:
        """Get PhotoImage for Tkinter with caching."""
        actual_zoom = self.get_actual_zoom()
        cache_key = round(actual_zoom, 3)
        
        # Check cache
        if cache_key in self._photo_cache:
            return self._photo_cache[cache_key]
        
        # Create new PhotoImage
        zoomed = self.get_zoomed_image()
        photo = ImageTk.PhotoImage(zoomed)
        
        # Clean up current photo
        if self._current_photo:
            try:
                del self._current_photo
            except Exception:
                pass
        
        self._current_photo = photo
        
        # Cache with size limit
        if len(self._photo_cache) >= MAX_CACHE_PHOTOS:
            old_key = min(self._photo_cache.keys())
            try:
                del self._photo_cache[old_key]
            except Exception:
                pass
        
        self._photo_cache[cache_key] = photo
        
        # Periodic garbage collection
        if len(self._photo_cache) % 2 == 0:
            gc.collect()
        
        return photo
    
    def clear_cache(self) -> None:
        """Clear all caches to free memory."""
        self._image_cache.clear()
        
        for photo in self._photo_cache.values():
            try:
                del photo
            except Exception:
                pass
        self._photo_cache.clear()
        
        if self._current_photo:
            try:
                del self._current_photo
                self._current_photo = None
            except Exception:
                pass
        
        gc.collect()
