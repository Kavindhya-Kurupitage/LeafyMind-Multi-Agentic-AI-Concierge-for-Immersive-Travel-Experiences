"""Unsplash API client for food dish imagery."""

import asyncio
import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


class UnsplashService:
    """Fetch food photos from Unsplash with in-memory caching."""

    def __init__(self) -> None:
        self.access_key = settings.unsplash_access_key.strip()
        self.base_url = settings.unsplash_base_url.rstrip("/")
        self._session = httpx.AsyncClient(timeout=5.0)
        self._cache: dict[str, dict[str, Any] | None] = {}

    @property
    def is_configured(self) -> bool:
        """True when UNSPLASH_ACCESS_KEY is set (non-placeholder)."""
        key = self.access_key
        if not key:
            return False
        lowered = key.lower()
        return lowered not in ("", "your_unsplash_access_key_here", "placeholder")

    async def get_food_image(self, dish_name: str) -> dict[str, Any] | None:
        """
        Search Unsplash for a food image matching dish_name.
        Returns dict with: url, alt_text, photographer, unsplash_link
        Returns None if API fails or no results found.
        Never raise exceptions — always fail gracefully.
        """
        cache_key = dish_name.lower().strip()
        if not cache_key:
            return None
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self.is_configured:
            logger.debug("UNSPLASH_ACCESS_KEY not set; skipping image fetch for %s", dish_name)
            self._cache[cache_key] = None
            return None

        try:
            query = f"{dish_name} sri lankan food"
            response = await self._session.get(
                f"{self.base_url}/search/photos",
                headers={"Authorization": f"Client-ID {self.access_key}"},
                params={"query": query, "per_page": 1, "orientation": "landscape"},
            )
            if response.status_code == 200:
                data = response.json()
                results = data.get("results") or []
                if results:
                    photo = results[0]
                    urls = photo.get("urls") or {}
                    user = photo.get("user") or {}
                    links = photo.get("links") or {}
                    result = {
                        "url": urls.get("small"),
                        "alt_text": photo.get("alt_description") or dish_name,
                        "photographer": user.get("name") or "Unsplash",
                        "unsplash_link": links.get("html") or "https://unsplash.com",
                    }
                    if result["url"]:
                        self._cache[cache_key] = result
                        logger.info("Unsplash image cached for dish: %s", dish_name)
                        return result
            else:
                logger.warning(
                    "Unsplash API returned %s for %s: %s",
                    response.status_code,
                    dish_name,
                    response.text[:200],
                )
        except Exception as exc:
            logger.warning("Unsplash fetch failed for %s: %s", dish_name, exc)

        self._cache[cache_key] = None
        return None

    async def get_images_for_dishes(self, dish_names: list[str]) -> dict[str, dict[str, Any] | None]:
        """Fetch images for multiple dishes concurrently."""
        if not dish_names:
            return {}
        tasks = [self.get_food_image(name) for name in dish_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            dish_names[i]: (results[i] if not isinstance(results[i], Exception) else None)
            for i in range(len(dish_names))
        }

    async def aclose(self) -> None:
        """Close the HTTP client (optional cleanup)."""
        await self._session.aclose()


unsplash_service = UnsplashService()
