"""Module for downloading images from URLs."""

import re
import urllib.error
import urllib.request
from io import BytesIO

from PIL import Image


def clean_url(url: str) -> str:
    """
    Clean URL by removing escape characters and fixing common issues.
    
    Args:
        url: The URL string that may contain escape characters
        
    Returns:
        Cleaned URL string
    """
    # Remove backslash escapes (common when URLs are passed from shell)
    url = url.replace('\\?', '?')
    url = url.replace('\\&', '&')
    url = url.replace('\\=', '=')
    url = url.replace('\\#', '#')
    
    # Only remove backslashes before special URL characters
    url = re.sub(r'\\([?&#=])', r'\1', url)
    
    # Strip whitespace
    url = url.strip()
    
    # Remove quotes if present
    if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
        url = url[1:-1]
    
    return url


def download_image_from_url(url: str) -> bytes:
    """
    Download an image from a URL and return the raw bytes.
    
    Args:
        url: The URL of the image to download
        
    Returns:
        Raw bytes containing the image data
        
    Raises:
        urllib.error.URLError: If the URL cannot be accessed
        ValueError: If the downloaded data is not a valid image
    """
    try:
        # Clean the URL first
        clean_url_str = clean_url(url)
        
        # Create a request with a user agent to avoid blocking
        req = urllib.request.Request(
            clean_url_str,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        # Download the image
        with urllib.request.urlopen(req, timeout=10) as response:
            image_data = response.read()
        
        # Verify it's an image by trying to open it
        image_buffer = BytesIO(image_data)
        try:
            Image.open(image_buffer).verify()
        finally:
            image_buffer.close()
        
        return image_data
        
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP Error {e.code}: {e.reason}. URL: {clean_url(url)}")
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to download image from URL: {str(e)}. URL: {clean_url(url)}")
    except Exception as e:
        raise ValueError(f"Invalid image data from URL: {str(e)}")
