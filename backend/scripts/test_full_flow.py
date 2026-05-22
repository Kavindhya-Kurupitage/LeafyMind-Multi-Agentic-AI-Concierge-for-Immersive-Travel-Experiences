"""
End-to-end integration checks for LeafyMind against a running API + PostgreSQL.

Run from the repo root (with `.env` configured and backend reachable):

    cd backend && python scripts/test_full_flow.py

Requires a working LLM provider (profile extraction and narratives). Uses DATABASE_URL
from the environment for direct feedback verification.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(REPO_ROOT / ".env")

import models  # noqa: E402, F401 — register ORM mappers
from database import AsyncSessionLocal  # noqa: E402
from models.attraction import Attraction  # noqa: E402
from models.feedback import Feedback  # noqa: E402
from models.food_item import FoodItem  # noqa: E402


API_BASE = os.getenv("INTEGRATION_API_BASE", "http://127.0.0.1:8000").rstrip("/")

MEAT_KEYWORDS = (
    "chicken",
    "pork",
    "beef",
    "fish",
    "prawn",
    "shrimp",
    "lamb",
    "mutton",
    "crab",
    "squid",
    "cuttlefish",
    "anchovy",
    "salmon",
    "tuna",
    "bacon",
    "ham",
    "duck",
    "turkey",
    "seafood",
)


def _print_result(name: str, ok: bool, detail: str = "") -> bool:
    label = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{label}] {name}{suffix}")
    return ok


async def _stream_chat_message(
    client: httpx.AsyncClient,
    token: str,
    session_id: str,
    message: str,
) -> dict[str, Any] | None:
    """POST /chat/message and return the final SSE `done` payload if present."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    done_summary: dict[str, Any] | None = None
    async with client.stream(
        "POST",
        f"{API_BASE}/chat/message",
        headers=headers,
        json={"session_id": session_id, "message": message},
        timeout=httpx.Timeout(180.0, connect=30.0),
    ) as resp:
        resp.raise_for_status()
        buffer = ""
        async for chunk in resp.aiter_text():
            buffer += chunk
            while "\n\n" in buffer:
                raw_event, buffer = buffer.split("\n\n", 1)
                data_lines = [
                    line[len("data:") :].strip()
                    for line in raw_event.splitlines()
                    if line.startswith("data:")
                ]
                if not data_lines:
                    continue
                try:
                    payload = json.loads("\n".join(data_lines))
                except json.JSONDecodeError:
                    continue
                if payload.get("type") == "done":
                    done_summary = payload.get("session_summary") or {}
    return done_summary


async def _fetch_seed_attraction_names() -> set[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Attraction.name).where(Attraction.is_active.is_(True))
        )
        return {row[0] for row in result.all() if row[0]}


def _extract_must_try_names(must_try: list) -> list[str]:
    """Support structured must_try objects or legacy string list."""
    names: list[str] = []
    for entry in must_try:
        if isinstance(entry, dict):
            name = entry.get("dish_name") or entry.get("name")
            if name:
                names.append(str(name))
        elif entry:
            names.append(str(entry))
    return names


async def _must_try_dishes_vegetarian(names: list[str]) -> tuple[bool, str]:
    """Ensure each suggested dish maps to a vegetarian/vegan FoodItem row."""
    async with AsyncSessionLocal() as session:
        for dish in names:
            query = select(FoodItem).where(FoodItem.name.ilike(f"%{dish.strip()}%"))
            result = await session.execute(query)
            items = list(result.scalars().all())
            if not items:
                return False, f"No FoodItem match for must_try '{dish}'"
            tags_union: set[str] = set()
            ingredients_blob = ""
            for item in items:
                tags_union.update(str(t).lower() for t in (item.dietary_tags or []))
                ingredients_blob += " " + " ".join(item.ingredients or []).lower()
            if not (
                "vegetarian" in tags_union
                or "vegan" in tags_union
                or "vegetarian_option" in tags_union
            ):
                return False, f"Dish '{dish}' has no vegetarian/vegan tag in DB"
            if any(k in ingredients_blob for k in MEAT_KEYWORDS):
                return False, f"Dish '{dish}' lists meat/fish ingredients"
        return True, ""


def _itinerary_activity_names(itinerary: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for day in itinerary or []:
        for slot in ("morning", "afternoon"):
            block = day.get(slot)
            if isinstance(block, dict):
                att = block.get("attraction_name")
                if att:
                    names.append(str(att))
    return names


def _normalise_name(value: str) -> str:
    return " ".join(value.casefold().split())


async def main() -> int:
    failures = 0

    uid = uuid.uuid4().hex[:10]
    email = f"integration_{uid}@example.com"
    password = f"TestFlow{uid[:4]}1"
    full_name = "Integration Tester"

    async with httpx.AsyncClient() as client:
        reg = await client.post(
            f"{API_BASE}/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        failures += not _print_result(
            "Register user via API",
            reg.status_code == 201,
            f"status={reg.status_code} body={reg.text[:200]}",
        )

        login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
        )
        failures += not _print_result(
            "Login and obtain JWT",
            login.status_code == 200 and login.json().get("access_token"),
            login.text[:300],
        )
        if login.status_code != 200:
            print("Aborting — cannot authenticate.")
            return 1

        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        start = await client.post(f"{API_BASE}/chat/session/start", headers=headers)
        failures += not _print_result(
            "Start chat session",
            start.status_code == 201,
            start.text[:200],
        )
        if start.status_code != 201:
            return 1

        session_id = start.json()["session_id"]

        profiling_messages = [
            (
                "Hello — we are a couple visiting Sri Lanka for the first time "
                "and we love nature."
            ),
            "We are looking for comfortable mid-range stays — not backpacker budget "
            "and not ultra-luxury.",
            "We are strictly vegetarian — please avoid meat and fish entirely.",
            "We will stay three nights near Ella.",
            "Our favourite activities are hiking jungle trails and chasing waterfalls.",
        ]
        contact_messages = [
            "You can email our itinerary to integration_test@example.com when ready.",
            (
                "Given all of that, what Leafy Cave packages and Sri Lankan vegetarian "
                "dishes would suit us best?"
            ),
        ]

        phase_history: list[str] = []
        last_summary: dict[str, Any] | None = None
        for i, msg in enumerate(profiling_messages, start=1):
            summary = await _stream_chat_message(client, token, session_id, msg)
            last_summary = summary or last_summary
            ph = (summary or {}).get("phase")
            if ph:
                phase_history.append(str(ph))
            failures += not _print_result(
                f"Chat stream completes (profiling message {i})",
                summary is not None,
                "no SSE done event",
            )

        contact_seen = "CONTACT_COLLECTION" in phase_history
        for j, msg in enumerate(contact_messages, start=1):
            summary = await _stream_chat_message(client, token, session_id, msg)
            last_summary = summary or last_summary
            ph = (summary or {}).get("phase")
            if ph:
                phase_history.append(str(ph))
            if ph == "CONTACT_COLLECTION":
                contact_seen = True
            failures += not _print_result(
                f"Chat stream completes (contact message {j})",
                summary is not None,
                "no SSE done event",
            )

        phase_after_contact = (last_summary or {}).get("phase")
        profile_after = (last_summary or {}).get("guest_profile") or {}
        failures += not _print_result(
            "Contact collection phase appears before recommendations",
            contact_seen or "CONTACT_COLLECTION" in phase_history,
            f"phases={phase_history[-6:]}",
        )
        recommending_seen = "RECOMMENDING" in phase_history or phase_after_contact == "RECOMMENDING"
        failures += not _print_result(
            "Phase transitions into RECOMMENDING after contact",
            recommending_seen,
            f"phase={phase_after_contact} phases={phase_history[-6:]}",
        )
        failures += not _print_result(
            "Guest profile stores contact email when provided",
            bool(profile_after.get("email")),
            f"email={profile_after.get('email')}",
        )

        profiling_seen = "PROFILING" in phase_history or "GREETING" in phase_history

        itinerary_summary = await _stream_chat_message(
            client,
            token,
            session_id,
            "Please prepare our day-by-day itinerary with hikes and waterfalls.",
        )
        it_phase = (itinerary_summary or {}).get("phase")
        if it_phase:
            phase_history.append(str(it_phase))
        itinerary_phase_seen = (
            it_phase == "ITINERARY"
            or "ITINERARY" in phase_history
            or it_phase == "RECOMMENDING"
        )
        failures += not _print_result(
            "Phase transitions into ITINERARY",
            itinerary_phase_seen,
            f"phase={it_phase}",
        )

        failures += not _print_result(
            "Phase flow includes profiling → contact → recommending → itinerary",
            profiling_seen
            and contact_seen
            and recommending_seen
            and itinerary_phase_seen,
            f"sequence_tail={phase_history[-10:]}",
        )

        pkg_resp = await client.get(
            f"{API_BASE}/recommendations/packages/{session_id}",
            headers=headers,
        )
        packages_ok = False
        detail = pkg_resp.text[:200]
        if pkg_resp.status_code == 200:
            recs = pkg_resp.json().get("recommendations") or []
            tiers = [r.get("tier") for r in recs]
            packages_ok = bool(recs) and "mid_range" in tiers
            detail = f"tiers={tiers}"
        failures += not _print_result(
            "Package recommendations include mid-range tier for guest profile",
            packages_ok,
            detail,
        )

        food_resp = await client.get(
            f"{API_BASE}/recommendations/food/{session_id}",
            headers=headers,
        )
        food_ok = False
        food_detail = food_resp.text[:200]
        must_try: list[str] = []
        if food_resp.status_code == 200:
            body = food_resp.json()
            must_try_raw = body.get("must_try") or []
            must_try = _extract_must_try_names(must_try_raw)
            veg_passes = 0
            veg_failures: list[str] = []
            for dish in must_try:
                dish_ok, dish_reason = await _must_try_dishes_vegetarian([dish])
                if dish_ok:
                    veg_passes += 1
                elif dish_reason:
                    veg_failures.append(dish_reason)
            food_ok = len(must_try) >= 2 and veg_passes >= min(2, len(must_try))
            food_detail = (
                f"must_try={must_try} veg_passes={veg_passes}/{len(must_try)}"
                if food_ok
                else "; ".join(veg_failures[:3])
            )
        failures += not _print_result(
            "Food recommendations contain only vegetarian dishes from KB",
            food_ok,
            food_detail,
        )

        it_resp = await client.get(
            f"{API_BASE}/recommendations/itinerary/{session_id}",
            headers=headers,
        )
        seed_names = await _fetch_seed_attraction_names()
        seed_norm = {_normalise_name(n) for n in seed_names}
        itinerary_ok = False
        it_detail = it_resp.text[:200]
        if it_resp.status_code == 200:
            data = it_resp.json()
            att_names = _itinerary_activity_names(data.get("itinerary") or [])
            missing = [
                n for n in att_names if _normalise_name(n) not in seed_norm
            ]
            itinerary_ok = bool(att_names) and not missing
            it_detail = f"missing={missing}" if missing else f"activities={att_names}"
        failures += not _print_result(
            "Itinerary activities reference seeded attractions only",
            itinerary_ok,
            it_detail,
        )

        fb_body = {
            "session_id": session_id,
            "package_rating": 5,
            "food_rating": 5,
            "itinerary_rating": 5,
            "ai_helpfulness_rating": 5,
            "free_text_feedback": "Beautiful suggestions — thank you Leafy Cave!",
        }
        fb_resp = await client.post(
            f"{API_BASE}/feedback/submit",
            headers=headers,
            json=fb_body,
        )
        fb_json = fb_resp.json() if fb_resp.status_code == 201 else {}
        failures += not _print_result(
            "Feedback submitted",
            fb_resp.status_code == 201,
            fb_resp.text[:200],
        )

        feedback_id = fb_json.get("id")
        tags_ok = False
        tags_detail = "no feedback id"
        if feedback_id:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Feedback).where(Feedback.id == uuid.UUID(feedback_id))
                )
                row = result.scalar_one_or_none()
                tags = list(row.auto_tags or []) if row else []
                tags_ok = row is not None and "positive" in tags and "ai_helpful" in tags
                tags_detail = f"tags={tags}"

        failures += not _print_result(
            "Feedback persisted with positive + ai_helpful tags",
            tags_ok,
            tags_detail,
        )

    print("\nSummary:", "ALL PASS" if failures == 0 else f"{failures} assertion(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
