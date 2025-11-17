import base64
import json
import logging
import mimetypes
import os
import time
from typing import Tuple
from urllib.parse import parse_qs, urlparse

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

    # Handle accidental duplication (e.g., "AIza...AIza...")
    # Look for the pattern where a key might be repeated
    # Gemini API keys typically start with "AIza" and are ~39 characters
    # If we see "AIza" twice, take the first occurrence
    if key.count("AIza") > 1:
        # Find the first occurrence and extract a reasonable key length
        first_aiza = key.find("AIza")
        # Typical API key length is around 39 chars, but we'll be generous
        # Extract up to 50 chars from the first "AIza" occurrence
        potential_key = key[first_aiza:first_aiza + 50]
        # If it looks like a valid key (starts with AIza and has reasonable length)
        if len(potential_key) >= 20:  # Minimum reasonable key length
            key = potential_key
            logger.debug("Detected duplicated API key, using first occurrence")

    # Final cleanup: remove any remaining trailing characters that aren't part of the key
    # API keys are alphanumeric with some special chars, typically end with alphanumeric
    # Remove trailing non-alphanumeric characters except if they're part of the key
    key = key.rstrip("&?# ")

    logger.debug("API key normalized (length: %d, starts with: %s)", len(key), key[:10] if len(key) >= 10 else key)
    return key


def _fetch_with_backoff(url: str, headers: dict, payload: dict, retries: int = 5, delay: float = 1.0) -> dict:
    """
    Call the Gemini API with exponential backoff to survive transient errors.
    """
    backoff = delay
    for attempt in range(retries):
        logger.debug("Gemini request attempt %s/%s", attempt + 1, retries)
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
            if response.status_code == 200:
                logger.debug("Gemini request succeeded on attempt %s", attempt + 1)
                return response.json()

            if response.status_code == 429 or response.status_code >= 500:
                logger.warning(
                    "Gemini transient error (status %s). Retrying in %.1fs",
                    response.status_code,
                    backoff,
                )
                if attempt == retries - 1:
                    break
                time.sleep(backoff)
                backoff *= 2
                continue

            raise GeminiServiceError(
                f"Gemini API error (status {response.status_code}): {response.text}"
            )
        except requests.exceptions.RequestException as exc:
            logger.warning("Gemini request exception: %s", exc)
            if attempt == retries - 1:
                raise GeminiServiceError(f"Failed to reach Gemini API: {exc}") from exc
            time.sleep(backoff)
            backoff *= 2

    raise GeminiServiceError("Exceeded retry budget when calling Gemini API.")


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
    base64_image, mime_type = _encode_image(image_path)
    url = f"{DEFAULT_MODEL_URL}?key={normalized_key}"
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

    logger.debug("Gemini response returned inline image data (%s bytes)", len(base64_data))

    return base64.b64decode(base64_data)

