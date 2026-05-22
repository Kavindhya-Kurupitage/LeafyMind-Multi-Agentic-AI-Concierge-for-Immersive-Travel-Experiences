"""Verify required external services and local assets are configured."""

import asyncio
import sys
from pathlib import Path

from config import settings
from services.email_service import email_service
from services.food_image_service import food_image_service
from services.unsplash_service import unsplash_service

PLACEHOLDER_MARKERS = ("REPLACE_", "your_", "change_me", "paste_")


def _is_placeholder(value: str) -> bool:
    v = (value or "").strip().lower()
    if not v:
        return True
    return any(m in v for m in PLACEHOLDER_MARKERS)


def _check_env() -> list[tuple[str, bool, str]]:
    rows: list[tuple[str, bool, str]] = []

    rows.append(
        (
            "GROQ_API_KEY",
            not _is_placeholder(settings.groq_api_key),
            "required for all AI agents",
        )
    )
    rows.append(
        (
            "UNSPLASH_ACCESS_KEY",
            not _is_placeholder(settings.unsplash_access_key),
            "food photo fallback",
        )
    )
    rows.append(
        (
            "OPENTRIPMAP_API_KEY",
            not _is_placeholder(settings.opentripmap_api_key),
            "itinerary discoveries",
        )
    )
    rows.append(
        (
            "GMAIL_SENDER_ADDRESS",
            not _is_placeholder(settings.gmail_sender_address),
            "feedback emails",
        )
    )
    rows.append(
        (
            "GMAIL_APP_PASSWORD",
            not _is_placeholder(settings.gmail_app_password),
            "feedback emails",
        )
    )
    rows.append(
        (
            "FRONTEND_URL",
            bool(settings.frontend_url.strip()),
            f"links in emails → {settings.frontend_url}",
        )
    )
    return rows


def _check_local_food_images() -> tuple[bool, str]:
    images_dir = Path(settings.food_images_dir)
    if not images_dir.is_dir():
        return False, f"directory missing: {images_dir}"
    files = [
        f
        for f in images_dir.iterdir()
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]
    if not files:
        return (
            False,
            "no image files — add photos to frontend/public/images/food/ "
            "(see README.md there)",
        )
    return True, f"{len(files)} local food image(s) found"


async def _test_unsplash() -> tuple[bool, str]:
    if _is_placeholder(settings.unsplash_access_key):
        return False, "UNSPLASH_ACCESS_KEY not set"
    result = await unsplash_service.get_food_image("Rice and Curry")
    if result and result.get("url"):
        return True, "API returned an image URL"
    return False, "API call failed or no results — check key and rate limits"


async def _test_opentripmap() -> tuple[bool, str]:
    if _is_placeholder(settings.opentripmap_api_key):
        return False, "OPENTRIPMAP_API_KEY not set"
    from services.opentripmap_service import opentripmap_service

    places = await opentripmap_service.search_nearby_places(
        kinds=["natural", "cultural"],
        radius_km=30,
        limit=3,
    )
    if places:
        return True, f"API returned {len(places)} place(s) near cabana"
    return False, "API returned no places — check key or coordinates"


def main() -> int:
    print("LeafyMind external services check\n" + "=" * 40)

    failed = 0

    print("\n[Environment variables]")
    for name, ok, note in _check_env():
        status = "OK" if ok else "MISSING"
        print(f"  {status:7} {name} — {note}")
        if not ok:
            failed += 1

    print("\n[Local food images]")
    ok, msg = _check_local_food_images()
    print(f"  {'OK' if ok else 'MISSING':7} {msg}")
    if not ok:
        failed += 1

    sample = food_image_service.resolve_local("Egg Hoppers")
    if sample:
        print(f"  OK      sample resolve: {sample['url']}")
    else:
        print("  WARN    Egg Hoppers — no local file (Unsplash will be used if configured)")

    print("\n[Email service]")
    if email_service.is_configured:
        print("  OK      Gmail SMTP credentials present")
    else:
        print("  MISSING Gmail not configured")
        failed += 1

    async def run_api_tests() -> None:
        nonlocal failed
        print("\n[Unsplash API]")
        ok, msg = await _test_unsplash()
        print(f"  {'OK' if ok else 'FAIL':7} {msg}")
        if not ok:
            failed += 1

        print("\n[OpenTripMap API]")
        ok, msg = await _test_opentripmap()
        print(f"  {'OK' if ok else 'FAIL':7} {msg}")
        if not ok:
            failed += 1

        await unsplash_service.aclose()
        from services.opentripmap_service import opentripmap_service

        await opentripmap_service.aclose()

    asyncio.run(run_api_tests())

    print("\n" + "=" * 40)
    if failed:
        print(f"FAILED: {failed} check(s) need attention.")
        print("Guide: docs/EXTERNAL_SERVICES_SETUP.md")
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
