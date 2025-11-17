import base64
import json
import logging
import mimetypes
import os
import random
import time
from typing import Tuple
from urllib.parse import parse_qs, urlparse

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None
    logger = logging.getLogger(__name__)
    logger.warning("google-genai package not found. Falling back to direct HTTP requests.")

import requests

logger = logging.getLogger(__name__)

DEFAULT_MODEL_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.5-flash-image:generateContent"
)


class GeminiServiceError(RuntimeError):
    """Raised when the Gemini service returns an error response."""


def _normalize_api_key(raw_key: str) -> str:
    """
    Accept keys that might include full URLs, query params, or accidental duplication.
    
    Handles cases like:
    - Full URLs: "https://...?key=AIza..."
    - Query strings: "key=AIza..." or "&key=AIza..."
    - Accidental duplication: "AIza...AIza..."
    - Trailing characters, whitespace, etc.
    """
    if not raw_key:
        return ""

    key = raw_key.strip()

    # If the user pastes the full Google endpoint or any URL, extract the key query param.
    if key.startswith(("http://", "https://")):
        parsed = urlparse(key)
        query_key = parse_qs(parsed.query).get("key")
        if query_key:
            key = query_key[0]
            logger.debug("Extracted API key from URL query parameter")

    # Handle snippets like "key=AIza..." or "&key=AIza..."
    if "key=" in key:
        # Split on "key=" and take everything after it
        parts = key.split("key=", 1)
        if len(parts) > 1:
            key = parts[1]
            logger.debug("Extracted API key from 'key=' pattern")
        # Drop any trailing query parameters, fragments, or whitespace
        key = key.split("&")[0].split("#")[0].split("?")[0].strip()

    # Find the first valid API key pattern (starts with "AIza")
    # This handles cases where there's junk before/after the actual key
    if "AIza" in key:
        first_aiza = key.find("AIza")
        # Extract from "AIza" onwards, stopping at invalid characters
        potential_key = key[first_aiza:]
        
        # Extract only valid API key characters
        # API keys typically contain: A-Z, a-z, 0-9, and some special chars like -_=
        # Stop at first invalid character (whitespace, newline, etc.)
        valid_chars = []
        for char in potential_key:
            if char.isalnum() or char in "-_=":
                valid_chars.append(char)
            elif char.isspace() or ord(char) < 32:  # Stop at whitespace or control chars
                break
            else:
                # Stop at other invalid characters
                break
        
        key = "".join(valid_chars)
        logger.debug("Extracted API key starting with 'AIza'")
    else:
        # No "AIza" found, try to extract valid characters anyway
        # Extract only valid API key characters
        valid_chars = []
        for char in key:
            if char.isalnum() or char in "-_=":
                valid_chars.append(char)
            elif char.isspace() or ord(char) < 32:  # Stop at whitespace or control chars
                break
            else:
                # Stop at other invalid characters
                break
        key = "".join(valid_chars)
    
    # Limit key length to reasonable maximum (60 chars should be more than enough)
    # Typical Gemini API keys are ~39 characters
    if len(key) > 60:
        logger.warning("API key seems too long (%d chars), truncating to 60", len(key))
        key = key[:60]
    
    # Validate that key starts with "AIza" (Gemini API keys start with this)
    if key and not key.startswith("AIza"):
        logger.warning("API key doesn't start with 'AIza', may be invalid")
    
    # Final cleanup: remove any trailing invalid characters
    key = key.rstrip("&?# ")

    logger.debug("API key normalized (length: %d, starts with: %s)", len(key), key[:10] if len(key) >= 10 else key)
    return key


def _fetch_with_backoff(url: str, headers: dict, payload: dict, retries: int = 5, delay: float = 2.0) -> dict:
    """
    Call the Gemini API with exponential backoff to survive transient errors.
    
    For 429 (rate limit) errors, uses longer initial delays and checks Retry-After header.
    """
    backoff = delay
    for attempt in range(retries):
        logger.debug("Gemini request attempt %s/%s", attempt + 1, retries)
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code == 200:
                logger.debug("Gemini request succeeded on attempt %s", attempt + 1)
                return response.json()

            if response.status_code == 429:
                # Rate limit error - check for Retry-After header
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    try:
                        wait_time = float(retry_after)
                        logger.warning(
                            "Gemini rate limit (429). Server suggests waiting %.1fs. Retrying...",
                            wait_time,
                        )
                        if attempt == retries - 1:
                            break
                        time.sleep(wait_time)
                        # Reset backoff after using Retry-After
                        backoff = delay
                        continue
                    except (ValueError, TypeError):
                        pass  # Fall through to exponential backoff
                
                # Use longer backoff for rate limits (start at 5s, double each time)
                rate_limit_backoff = max(5.0, backoff * 2.5)
                # Add jitter to avoid thundering herd
                jitter = random.uniform(0.5, 1.5)
                wait_time = rate_limit_backoff * jitter
                
                logger.warning(
                    "Gemini rate limit (429). Retrying in %.1fs (attempt %s/%s)",
                    wait_time,
                    attempt + 1,
                    retries,
                )
                if attempt == retries - 1:
                    break
                time.sleep(wait_time)
                backoff = rate_limit_backoff
                continue

            if response.status_code >= 500:
                logger.warning(
                    "Gemini server error (status %s). Retrying in %.1fs",
                    response.status_code,
                    backoff,
                )
                if attempt == retries - 1:
                    break
                # Add jitter for server errors too
                jitter = random.uniform(0.8, 1.2)
                time.sleep(backoff * jitter)
                backoff *= 2
                continue

            raise GeminiServiceError(
                f"Gemini API error (status {response.status_code}): {response.text}"
            )
        except requests.exceptions.RequestException as exc:
            logger.warning("Gemini request exception: %s", exc)
            if attempt == retries - 1:
                raise GeminiServiceError(f"Failed to reach Gemini API: {exc}") from exc
            # Add jitter for network errors
            jitter = random.uniform(0.8, 1.2)
            time.sleep(backoff * jitter)
            backoff *= 2

    raise GeminiServiceError(
        "Exceeded retry budget when calling Gemini API. "
        "You may be rate limited - please wait a few minutes and try again."
    )


def _encode_image(image_path: str) -> Tuple[str, str]:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    logger.debug("Encoding image at %s", image_path)

    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith("image/"):
        raise ValueError(f"Unsupported image MIME type for: {image_path}")

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return encoded, mime_type


def generate_image_edit(api_key: str, prompt: str, image_path: str) -> bytes:
    """
    Submit the provided image and prompt to Gemini and return the generated bytes.
    
    Uses the official Google Generative AI SDK if available, otherwise falls back to direct HTTP requests.
    """
    if not api_key:
        raise ValueError("API key is required.")
    if not prompt:
        raise ValueError("Prompt is required.")

    # Normalize the API key to handle URLs, query strings, or accidental duplication
    normalized_key = _normalize_api_key(api_key)
    if not normalized_key:
        raise ValueError("API key is required (normalization resulted in empty key).")

    logger.debug("Preparing Gemini image edit call for %s", image_path)
    
    # Try using the official SDK first
    if genai is not None:
        try:
            return _generate_with_sdk(normalized_key, prompt, image_path)
        except Exception as exc:
            logger.warning("SDK generation failed, falling back to HTTP: %s", exc)
            # Fall through to HTTP method
    
    # Fallback to direct HTTP requests
    return _generate_with_http(normalized_key, prompt, image_path)


def _generate_with_sdk(api_key: str, prompt: str, image_path: str) -> bytes:
    """Generate image using the official Google Generative AI SDK."""
    logger.debug("Using Google Generative AI SDK")
    
    # Read image file
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/png"
    
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    
    # Create client
    client = genai.Client(api_key=api_key)
    
    # Prepare contents - SDK expects Content objects or a list format
    # Based on SDK docs, contents should be a list of Content objects or compatible format
    try:
        # Try using SDK types if available
        if types is not None:
            # Check what types are available
            if hasattr(types, "Part") and hasattr(types, "Blob"):
                # Use proper SDK types
                contents = [
                    types.Part(text=prompt),
                    types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=base64.b64encode(image_data).decode("utf-8")
                        )
                    )
                ]
            elif hasattr(types, "Content") and hasattr(types, "Part"):
                # Alternative: wrap in Content
                contents = types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(
                            inline_data={
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_data).decode("utf-8")
                            }
                        )
                    ]
                )
            else:
                # Fallback: use dict format matching HTTP API
                contents = [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": base64.b64encode(image_data).decode("utf-8")
                            }
                        }
                    ]
                }]
        else:
            # No types module, use dict format
            contents = [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(image_data).decode("utf-8")
                        }
                    }
                ]
            }]
        
        # Generate content with image
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=contents,
            config={
                "response_modalities": ["IMAGE"]
            }
        )
    except Exception as exc:
        logger.error("SDK generate_content failed: %s", exc)
        logger.debug("Attempted contents format: %s, type: %s", contents, type(contents))
        # Re-raise to trigger fallback to HTTP
        raise GeminiServiceError(f"SDK generation failed: {exc}") from exc
    
    # Extract image data from response
    # Response structure may vary, try multiple access patterns
    try:
        logger.debug("Extracting image from SDK response. Response type: %s", type(response))
        
        # Try accessing via candidates (most common path)
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            logger.debug("Candidate found, type: %s", type(candidate))
            
            if hasattr(candidate, "content"):
                content = candidate.content
                logger.debug("Content found, type: %s", type(content))
                
                if hasattr(content, "parts"):
                    logger.debug("Parts found: %d parts", len(content.parts))
                    for i, part in enumerate(content.parts):
                        logger.debug("Part %d: type=%s, dir=%s", i, type(part), [x for x in dir(part) if not x.startswith('_')])
                        
                        # Try inline_data (snake_case)
                        if hasattr(part, "inline_data") and part.inline_data:
                            logger.debug("Found inline_data (snake_case)")
                            inline_data = part.inline_data
                            if hasattr(inline_data, "data"):
                                data = inline_data.data
                                logger.debug("Data found, type: %s, length: %d", type(data), len(data) if isinstance(data, (str, bytes)) else 0)
                                # Try decoding if it's a string
                                if isinstance(data, str):
                                    image_bytes = base64.b64decode(data)
                                elif isinstance(data, bytes):
                                    image_bytes = data
                                else:
                                    continue
                                logger.debug("SDK response returned image data (%s bytes)", len(image_bytes))
                                if len(image_bytes) > 1000:  # Sanity check - images should be larger
                                    return image_bytes
                                else:
                                    logger.warning("Image data too small (%d bytes), continuing search", len(image_bytes))
                        
                        # Try inlineData (camelCase)
                        if hasattr(part, "inlineData") and part.inlineData:
                            logger.debug("Found inlineData (camelCase)")
                            inline_data = part.inlineData
                            if hasattr(inline_data, "data"):
                                data = inline_data.data
                                logger.debug("Data found, type: %s, length: %d", type(data), len(data) if isinstance(data, (str, bytes)) else 0)
                                if isinstance(data, str):
                                    image_bytes = base64.b64decode(data)
                                elif isinstance(data, bytes):
                                    image_bytes = data
                                else:
                                    continue
                                logger.debug("SDK response returned image data (%s bytes)", len(image_bytes))
                                if len(image_bytes) > 1000:
                                    return image_bytes
        
        # Try accessing as dict-like structure
        if isinstance(response, dict):
            logger.debug("Response is dict-like")
            candidates = response.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    # Try both naming conventions
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if inline_data and "data" in inline_data:
                        data = inline_data["data"]
                        logger.debug("Found data in dict, type: %s", type(data))
                        if isinstance(data, str):
                            image_bytes = base64.b64decode(data)
                        elif isinstance(data, bytes):
                            image_bytes = data
                        else:
                            continue
                        logger.debug("SDK response returned image data (%s bytes)", len(image_bytes))
                        if len(image_bytes) > 1000:
                            return image_bytes
        
        # Try accessing response.text if it's an image (unlikely but possible)
        if hasattr(response, "text") and response.text:
            logger.debug("Trying response.text")
            try:
                image_bytes = base64.b64decode(response.text)
                logger.debug("SDK response returned image data from text (%s bytes)", len(image_bytes))
                if len(image_bytes) > 1000:
                    return image_bytes
            except Exception as exc:
                logger.debug("Failed to decode response.text: %s", exc)
        
    except Exception as exc:
        logger.error("Failed to extract image from SDK response: %s", exc, exc_info=True)
        logger.debug("Response type: %s, Response repr: %s", type(response), repr(response)[:500])
    
    raise GeminiServiceError("SDK response missing image data or image data too small")


def _generate_with_http(api_key: str, prompt: str, image_path: str) -> bytes:
    """Generate image using direct HTTP requests (fallback method)."""
    logger.debug("Using direct HTTP requests")
    
    base64_image, mime_type = _encode_image(image_path)
    url = f"{DEFAULT_MODEL_URL}?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {"inlineData": {"mimeType": mime_type, "data": base64_image}},
                ]
            }
        ],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }

    response = _fetch_with_backoff(url, headers, payload)

    base64_data = (
        response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("inlineData", {})
        .get("data")
    )

    if not base64_data:
        raise GeminiServiceError(f"Gemini response missing image data: {json.dumps(response, indent=2)}")

    logger.debug("HTTP response returned inline image data (%s bytes)", len(base64_data))

    return base64.b64decode(base64_data)

