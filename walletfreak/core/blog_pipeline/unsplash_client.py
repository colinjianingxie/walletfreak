"""Lightweight Unsplash API client for fetching featured images."""

import logging
import os
import requests

logger = logging.getLogger(__name__)


def search_photo(query: str) -> dict | None:
    """Search Unsplash for a landscape photo matching the query.

    Returns:
        Dict with {url, photographer, photographer_url} or None on failure.
    """
    access_key = os.environ.get('UNSPLASH_ACCESS_KEY')
    if not access_key:
        logger.warning("UNSPLASH_ACCESS_KEY not set, skipping image fetch")
        return None

    try:
        response = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "query": query,
                "orientation": "landscape",
                "per_page": 1,
            },
            headers={"Authorization": f"Client-ID {access_key}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return None

        photo = results[0]

        # Trigger download event per Unsplash API guidelines
        download_url = photo.get("links", {}).get("download_location")
        if download_url:
            try:
                requests.get(
                    download_url,
                    headers={"Authorization": f"Client-ID {access_key}"},
                    timeout=5,
                )
            except Exception:
                pass  # Non-critical

        return {
            "url": photo["urls"]["regular"],
            "photographer": photo["user"]["name"],
            "photographer_url": photo["user"]["links"]["html"],
        }

    except Exception as e:
        logger.error("Unsplash API error: %s", e)
        return None
