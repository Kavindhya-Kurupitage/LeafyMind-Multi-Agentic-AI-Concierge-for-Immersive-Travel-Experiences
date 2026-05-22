"""Tests for FoodImageService local-first resolution and Unsplash fallback."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from services.food_image_service import (
    FoodImageService,
    candidate_stems_for_dish,
    filename_stem_for_dish,
    slugify,
)


def test_slugify_normalizes_dish_name():
    assert slugify("Dhal Curry (Parippu)") == "dhal-curry-parippu"


def test_filename_stem_uses_leafy_cave_aliases():
    assert filename_stem_for_dish("Hoppers (Appam)") == "Hoppers"
    assert filename_stem_for_dish("Kottu Roti") == "Kottu-Roti"
    assert filename_stem_for_dish("Fish Ambul Thiyal") == "Ambul-Thiyal"


def test_resolve_local_case_insensitive_filename(tmp_path: Path):
    (tmp_path / "Kottu-Roti.jpg").write_bytes(b"fake")
    service = FoodImageService()
    service._images_dir = tmp_path
    service._url_prefix = "/images/food"

    result = service.resolve_local("Kottu Roti")
    assert result is not None
    assert result["url"].endswith("/images/food/Kottu-Roti.jpg")
    assert result["source"] == "local"


def test_resolve_local_maps_parippu_curry(tmp_path: Path):
    (tmp_path / "Parippu-Curry.jpg").write_bytes(b"fake")
    service = FoodImageService()
    service._images_dir = tmp_path
    service._url_prefix = "/images/food"

    result = service.resolve_local("Dhal Curry (Parippu)")
    assert result is not None
    assert "Parippu-Curry" in result["url"]


def test_resolve_local_returns_none_when_missing(tmp_path: Path):
    service = FoodImageService()
    service._images_dir = tmp_path

    assert service.resolve_local("Unknown Dish") is None


@pytest.mark.asyncio
async def test_get_food_image_skips_unsplash_when_local_exists(tmp_path: Path):
    (tmp_path / "Watalappam.jpg").write_bytes(b"fake")
    service = FoodImageService()
    service._images_dir = tmp_path
    service._url_prefix = "/images/food"

    with patch(
        "services.food_image_service.unsplash_service.get_food_image",
        new_callable=AsyncMock,
    ) as mock_unsplash:
        result = await service.get_food_image("Watalappan")
        mock_unsplash.assert_not_called()

    assert result["source"] == "local"
    assert result["url"].endswith("/images/food/Watalappam.jpg")


@pytest.mark.asyncio
async def test_get_food_image_unsplash_fallback_when_local_missing(tmp_path: Path):
    service = FoodImageService()
    service._images_dir = tmp_path
    service._url_prefix = "/images/food"

    unsplash_payload = {
        "url": "https://images.unsplash.com/photo-1",
        "alt_text": "Wood Apple Juice",
        "photographer": "Test",
        "unsplash_link": "https://unsplash.com/photos/1",
    }

    with patch(
        "services.food_image_service.unsplash_service.is_configured",
        True,
    ), patch(
        "services.food_image_service.unsplash_service.get_food_image",
        new_callable=AsyncMock,
        return_value=unsplash_payload,
    ) as mock_unsplash:
        result = await service.get_food_image("Wood Apple Juice")
        mock_unsplash.assert_called_once_with("Wood Apple Juice")

    assert result["source"] == "unsplash"
    assert result["url"].startswith("https://")


@pytest.mark.asyncio
async def test_get_images_for_dishes_no_unsplash_when_not_configured(tmp_path: Path):
    service = FoodImageService()
    service._images_dir = tmp_path

    with patch(
        "services.food_image_service.unsplash_service.is_configured",
        False,
    ), patch(
        "services.food_image_service.unsplash_service.get_images_for_dishes",
        new_callable=AsyncMock,
    ) as mock_batch:
        result = await service.get_images_for_dishes(["Wood Apple Juice"])
        mock_batch.assert_not_called()

    assert result["Wood Apple Juice"] is None


@pytest.mark.asyncio
async def test_get_images_for_dishes_mixed_local_and_unsplash(tmp_path: Path):
    (tmp_path / "Hoppers.jpg").write_bytes(b"fake")
    service = FoodImageService()
    service._images_dir = tmp_path
    service._url_prefix = "/images/food"

    unsplash_payload = {
        "url": "https://images.unsplash.com/photo-2",
        "alt_text": "Pol Sambol",
        "photographer": "Test",
        "unsplash_link": "https://unsplash.com/photos/2",
    }

    with patch(
        "services.food_image_service.unsplash_service.is_configured",
        True,
    ), patch(
        "services.food_image_service.unsplash_service.get_images_for_dishes",
        new_callable=AsyncMock,
        return_value={"Pol Sambol": unsplash_payload},
    ) as mock_batch:
        result = await service.get_images_for_dishes(["Hoppers (Appam)", "Pol Sambol"])
        mock_batch.assert_called_once_with(["Pol Sambol"])

    assert result["Hoppers (Appam)"]["source"] == "local"
    assert "Hoppers" in result["Hoppers (Appam)"]["url"]
    assert result["Pol Sambol"]["source"] == "unsplash"


def test_candidate_stems_includes_alias_and_slug():
    stems = candidate_stems_for_dish("Kottu Roti")
    assert stems[0] == "Kottu-Roti"
    assert "kottu-roti" in stems
