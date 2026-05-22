"""Resolve food dish images — local Leafy Cave photos first, then Unsplash."""

import logging
import re
from pathlib import Path
from typing import Any

from config import settings
from services.unsplash_service import unsplash_service

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

# Database dish name (lowercase) → filename stem in frontend/public/images/food/
DISH_FILENAME_ALIASES: dict[str, str] = {
    "rice and curry": "Red-Rice-and-Curry",
    "hoppers (appam)": "Hoppers",
    "hoppers": "Hoppers",
    "appam": "Hoppers",
    "egg hoppers": "Hoppers",
    "kottu roti": "Kottu-Roti",
    "dhal curry (parippu)": "Parippu-Curry",
    "dhal curry": "Parippu-Curry",
    "parippu": "Parippu-Curry",
    "pol sambol": "Gotukola-Sambol",
    "fish ambul thiyal": "Ambul-Thiyal",
    "string hoppers (idiyappam)": "String-Hoppers",
    "string hoppers": "String-Hoppers",
    "idiyappam": "String-Hoppers",
    "wood apple juice": "wood-apple-juice",
    "watalappan": "Watalappam",
}


def slugify(dish_name: str) -> str:
    """Convert a dish name to a filesystem-safe slug."""
    text = dish_name.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def _normalize_for_match(text: str) -> str:
    """Case-insensitive alphanumeric key for filename comparison."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def filename_stem_for_dish(dish_name: str) -> str:
    """Return the preferred filename stem for a dish (aliases override slugify)."""
    key = dish_name.lower().strip()
    if key in DISH_FILENAME_ALIASES:
        return DISH_FILENAME_ALIASES[key]
    return slugify(dish_name)


def candidate_stems_for_dish(dish_name: str) -> list[str]:
    """Ordered stems to try when resolving a local image file."""
    key = dish_name.lower().strip()
    stems: list[str] = []
    if key in DISH_FILENAME_ALIASES:
        stems.append(DISH_FILENAME_ALIASES[key])
    slug = slugify(dish_name)
    if slug and slug not in stems:
        stems.append(slug)
    return stems


class FoodImageService:
    """Local public images first; Unsplash fills gaps when local files are missing."""

    def __init__(self) -> None:
        self._images_dir = Path(settings.food_images_dir)
        self._url_prefix = settings.food_images_url_prefix.rstrip("/")
        self._file_index: dict[str, Path] | None = None

    def _build_file_index(self) -> dict[str, Path]:
        """Map normalized stem → actual file path (case-insensitive)."""
        index: dict[str, Path] = {}
        if not self._images_dir.is_dir():
            return index
        for path in self._images_dir.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            index[_normalize_for_match(path.stem)] = path
        return index

    def _file_index_cached(self) -> dict[str, Path]:
        if self._file_index is None:
            self._file_index = self._build_file_index()
        return self._file_index

    def refresh_file_index(self) -> None:
        """Clear cached directory listing (e.g. after adding new photos)."""
        self._file_index = None

    def _public_url(self, filename: str) -> str:
        """Absolute URL so dish images load from the Vite frontend origin."""
        base = settings.frontend_url.rstrip("/")
        return f"{base}{self._url_prefix}/{filename}"

    def _image_dict_from_path(self, path: Path, dish_name: str) -> dict[str, Any]:
        return {
            "url": self._public_url(path.name),
            "alt_text": dish_name,
            "source": "local",
            "photographer": None,
            "unsplash_link": None,
        }

    def _find_local_path(self, stem: str) -> Path | None:
        """Find a file for stem using exact name then case-insensitive index."""
        if not stem:
            return None
        for ext in IMAGE_EXTENSIONS:
            exact = self._images_dir / f"{stem}{ext}"
            if exact.is_file():
                return exact
        normalized = _normalize_for_match(stem)
        return self._file_index_cached().get(normalized)

    def _fuzzy_find_by_dish_words(self, dish_name: str) -> Path | None:
        """Match dish tokens to filenames (e.g. 'Fish Ambul Thiyal' → Ambul-Thiyal.jpg)."""
        words = [
            w
            for w in re.sub(r"[^\w\s]", " ", dish_name.lower()).split()
            if len(w) > 2 and w not in ("and", "the", "with", "for")
        ]
        if not words:
            return None
        best: tuple[int, Path] | None = None
        for path in self._file_index_cached().values():
            stem_norm = _normalize_for_match(path.stem)
            hits = sum(1 for w in words if w in stem_norm or stem_norm in w)
            if hits > 0 and (best is None or hits > best[0]):
                best = (hits, path)
        if best and best[0] >= max(1, len(words) // 2):
            return best[1]
        return None

    def resolve_local(self, dish_name: str) -> dict[str, Any] | None:
        """
        If a file exists under food_images_dir, return a browser-ready image dict.
        URL path matches Vite public dir: /images/food/<file>.
        """
        if not dish_name or not dish_name.strip():
            return None
        if not self._images_dir.is_dir():
            logger.debug("Food images directory missing: %s", self._images_dir)
            return None

        for stem in candidate_stems_for_dish(dish_name):
            path = self._find_local_path(stem)
            if path:
                return self._image_dict_from_path(path, dish_name)

        fuzzy = self._fuzzy_find_by_dish_words(dish_name)
        if fuzzy:
            return self._image_dict_from_path(fuzzy, dish_name)

        return None

    async def get_food_image(self, dish_name: str) -> dict[str, Any] | None:
        """Resolve one dish: local file, else Unsplash when configured."""
        local = self.resolve_local(dish_name)
        if local:
            return local

        if not unsplash_service.is_configured:
            logger.debug(
                "No local image for %r and UNSPLASH_ACCESS_KEY not set",
                dish_name,
            )
            return None

        unsplash = await unsplash_service.get_food_image(dish_name)
        if unsplash:
            unsplash = dict(unsplash)
            unsplash["source"] = "unsplash"
            logger.info("Unsplash fallback image for dish: %s", dish_name)
        return unsplash

    async def get_images_for_dishes(
        self, dish_names: list[str]
    ) -> dict[str, dict[str, Any] | None]:
        """Resolve images for multiple dishes; local wins, Unsplash fills gaps."""
        if not dish_names:
            return {}

        self.refresh_file_index()
        result: dict[str, dict[str, Any] | None] = {}
        need_unsplash: list[str] = []

        for name in dish_names:
            local = self.resolve_local(name)
            if local:
                result[name] = local
            else:
                need_unsplash.append(name)

        if not need_unsplash:
            return result

        if not unsplash_service.is_configured:
            logger.warning(
                "No local image for %d dish(es) and UNSPLASH_ACCESS_KEY is not set — "
                "add photos under frontend/public/images/food/ or set UNSPLASH_ACCESS_KEY in .env",
                len(need_unsplash),
            )
            for name in need_unsplash:
                result[name] = None
            return result

        fallback = await unsplash_service.get_images_for_dishes(need_unsplash)
        for name in need_unsplash:
            img = fallback.get(name)
            if img:
                img = dict(img)
                img["source"] = "unsplash"
                logger.info("Unsplash fallback image for dish: %s", name)
            else:
                logger.debug("Unsplash returned no image for dish: %s", name)
            result[name] = img

        return result


food_image_service = FoodImageService()
