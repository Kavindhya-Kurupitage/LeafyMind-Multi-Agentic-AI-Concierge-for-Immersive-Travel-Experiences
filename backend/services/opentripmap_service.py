"""OpenTripMap API client for discovering attractions near Wellawaya."""

import asyncio
import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)

# Max concurrent detail requests (free tier: 5 req/s)
_DETAIL_CONCURRENCY = 5


class OpenTripMapService:
    """Search and enrich nearby places around Leafy Cave cabana."""

    def __init__(self) -> None:
        self.api_key = settings.opentripmap_api_key.strip()
        self.base_url = settings.opentripmap_base_url.rstrip("/")
        self.cabana_lat = settings.cabana_lat
        self.cabana_lon = settings.cabana_lon
        self._session = httpx.AsyncClient(timeout=10.0)
        self._cache: dict[str, list[dict[str, Any]]] = {}

    async def search_nearby_places(
        self,
        kinds: list[str],
        radius_km: int = 50,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Search for places near the cabana by category.
        kinds: e.g. ["natural", "cultural", "parks"]
        Returns list of enriched place dicts.
        """
        if not self.api_key:
            logger.debug("OPENTRIPMAP_API_KEY not set; skipping place discovery")
            return []

        kinds_str = ",".join(k for k in kinds if k)
        cache_key = f"{kinds_str}_{radius_km}_{limit}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            response = await self._session.get(
                f"{self.base_url}/places/radius",
                params={
                    "radius": radius_km * 1000,
                    "lon": self.cabana_lon,
                    "lat": self.cabana_lat,
                    "kinds": kinds_str,
                    "limit": limit,
                    "format": "json",
                    "apikey": self.api_key,
                },
            )
            if response.status_code == 200:
                places = response.json()
                if not isinstance(places, list):
                    places = []
                enriched = await self._enrich_places(places)
                self._cache[cache_key] = enriched
                logger.info(
                    "OpenTripMap: %s places for kinds=%s radius=%skm",
                    len(enriched),
                    kinds_str,
                    radius_km,
                )
                return enriched
            logger.warning(
                "OpenTripMap search returned %s: %s",
                response.status_code,
                response.text[:200],
            )
        except Exception as exc:
            logger.warning("OpenTripMap search failed: %s", exc)

        return []

    async def _enrich_places(self, places: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fetch full details for each place including image and description."""
        xids = [p["xid"] for p in places if p.get("xid")]
        if not xids:
            return []

        semaphore = asyncio.Semaphore(_DETAIL_CONCURRENCY)

        async def fetch_one(xid: str) -> dict[str, Any] | None:
            async with semaphore:
                return await self._get_place_detail(xid)

        results = await asyncio.gather(
            *[fetch_one(xid) for xid in xids],
            return_exceptions=True,
        )
        enriched: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, dict) and result.get("name"):
                enriched.append(result)
        return enriched

    async def _get_place_detail(self, xid: str) -> dict[str, Any] | None:
        """Get full details for one place by its xid."""
        try:
            response = await self._session.get(
                f"{self.base_url}/places/xid/{xid}",
                params={"apikey": self.api_key},
            )
            if response.status_code == 200:
                data = response.json()
                preview = data.get("preview") or {}
                point = data.get("point") or {}
                return {
                    "xid": xid,
                    "name": data.get("name", "Unknown Place"),
                    "description": self._extract_description(data),
                    "kinds": data.get("kinds", ""),
                    "lat": point.get("lat"),
                    "lon": point.get("lon"),
                    "image_url": preview.get("source"),
                    "wikipedia_url": data.get("wikipedia"),
                    "source": "discovered",
                }
        except Exception as exc:
            logger.warning("Place detail fetch failed for %s: %s", xid, exc)
        return None

    @staticmethod
    def _extract_description(data: dict[str, Any]) -> str:
        """Extract best available description from place data."""
        wiki = data.get("wikipedia_extracts") or {}
        if wiki.get("text"):
            text = str(wiki["text"])
            return text[:300] + "..." if len(text) > 300 else text
        info = data.get("info") or {}
        descr = info.get("descr")
        if descr:
            text = str(descr)
            return text[:300] + "..." if len(text) > 300 else text
        return "A notable attraction near Wellawaya."

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._session.aclose()


opentripmap_service = OpenTripMapService()
