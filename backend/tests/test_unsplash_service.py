"""Tests for UnsplashService caching and graceful failure."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from services.unsplash_service import UnsplashService


@pytest.mark.asyncio
async def test_get_food_image_uses_cache():
    service = UnsplashService()
    service.access_key = "test-key"
    service._cache["kiribath"] = {
        "url": "https://images.unsplash.com/photo-1",
        "alt_text": "Kiribath",
        "photographer": "Test",
        "unsplash_link": "https://unsplash.com/photos/1",
    }

    result = await service.get_food_image("Kiribath")
    assert result is not None
    assert result["url"].startswith("https://images.unsplash.com")


@pytest.mark.asyncio
async def test_get_food_image_no_key_returns_none():
    service = UnsplashService()
    service.access_key = ""

    result = await service.get_food_image("Hoppers")
    assert result is None
    assert service._cache["hoppers"] is None


@pytest.mark.asyncio
async def test_get_food_image_api_failure_returns_none():
    service = UnsplashService()
    service.access_key = "test-key"
    service._session = MagicMock()
    service._session.get = AsyncMock(side_effect=RuntimeError("network down"))

    result = await service.get_food_image("String Hoppers")
    assert result is None
