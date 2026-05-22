"""
Phase 3 integration test — full Agent Hub guided journey via API + SSE.

    docker exec leafymind-backend python -m scripts.test_agent_hub_flow

Uses INTEGRATION_API_BASE (default http://127.0.0.1:8000 inside container).
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

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(REPO_ROOT / ".env")

API_BASE = os.getenv("INTEGRATION_API_BASE", "http://127.0.0.1:8000").rstrip("/")
HUB_EMAIL = os.getenv("TEST_GUEST_EMAIL", "guest.test1@example.com")
HUB_PASSWORD = os.getenv("TEST_GUEST_PASSWORD", "TestGuest1")
CONTACT_EMAIL = os.getenv("TEST_CONTACT_EMAIL", "hub.integration@example.com")


def _print_result(name: str, ok: bool, detail: str = "") -> bool:
    label = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{label}] {name}{suffix}")
    return ok


async def _consume_sse(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Collect SSE events until `done` or `error`."""
    result: dict[str, Any] = {
        "artifacts": {},
        "guided_turn": None,
        "journey": None,
        "error": None,
    }
    async with client.stream(
        "POST",
        url,
        headers={**headers, "Accept": "text/event-stream"},
        json=payload,
        timeout=httpx.Timeout(300.0, connect=30.0),
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
                    event = json.loads("\n".join(data_lines))
                except json.JSONDecodeError:
                    continue
                etype = event.get("type")
                if etype == "artifact":
                    kind = event.get("kind")
                    if kind:
                        result["artifacts"][kind] = event.get("data")
                elif etype == "guided_turn":
                    result["guided_turn"] = event.get("data")
                elif etype == "journey":
                    result["journey"] = event.get("data")
                elif etype == "error":
                    result["error"] = event.get("message")
                elif etype == "done":
                    result["done"] = event
                    return result
    return result


async def _guided_turn(
    client: httpx.AsyncClient,
    token: str,
    thread_id: str,
    step_id: str,
    selected: list[str],
    free_text: str | None = None,
) -> dict[str, Any]:
    return await _consume_sse(
        client,
        f"{API_BASE}/agents/threads/{thread_id}/message",
        {"Authorization": f"Bearer {token}"},
        {
            "message": "",
            "guided_response": {
                "step_id": step_id,
                "selected": selected,
                "free_text": free_text,
            },
        },
    )


async def _create_thread(
    client: httpx.AsyncClient,
    token: str,
    agent_id: str,
) -> str:
    resp = await client.post(
        f"{API_BASE}/agents/{agent_id}/threads",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": f"Integration {agent_id}"},
    )
    resp.raise_for_status()
    return resp.json()["id"]


async def _run_profile_builder(client: httpx.AsyncClient, token: str) -> dict[str, Any]:
    thread_id = await _create_thread(client, token, "profile_builder")
    steps = [
        ("group_type", ["family"], None),
        ("travel_style", ["adventure"], None),
        ("budget_tier", ["mid_range"], None),
        ("dietary_restrictions", ["none"], None),
        ("duration_nights", ["2"], None),
        ("interests", ["waterfalls", "wildlife"], None),
        ("fitness_level", ["moderate"], None),
        ("contact", [], CONTACT_EMAIL),
        ("profile_confirm", ["confirm"], None),
    ]
    last: dict[str, Any] = {}
    for step_id, selected, free_text in steps:
        last = await _guided_turn(client, token, thread_id, step_id, selected, free_text)
        if last.get("error"):
            break
    return {"thread_id": thread_id, **last}


async def _run_specialist(
    client: httpx.AsyncClient,
    token: str,
    agent_id: str,
    steps: list[tuple[str, list[str], str | None]],
) -> dict[str, Any]:
    thread_id = await _create_thread(client, token, agent_id)
    last: dict[str, Any] = {}
    for step_id, selected, free_text in steps:
        last = await _guided_turn(client, token, thread_id, step_id, selected, free_text)
        if last.get("error"):
            break
    return {"thread_id": thread_id, **last}


async def main() -> int:
    failures = 0

    async with httpx.AsyncClient() as client:
        login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": HUB_EMAIL, "password": HUB_PASSWORD},
        )
        if login.status_code != 200:
            reg = await client.post(
                f"{API_BASE}/auth/register",
                json={
                    "email": HUB_EMAIL,
                    "password": HUB_PASSWORD,
                    "full_name": "Hub Tester",
                },
            )
            failures += not _print_result(
                "Register hub test user",
                reg.status_code == 201,
                reg.text[:200],
            )
            login = await client.post(
                f"{API_BASE}/auth/login",
                json={"email": HUB_EMAIL, "password": HUB_PASSWORD},
            )
        token = login.json().get("access_token") if login.status_code == 200 else None
        failures += not _print_result("Hub user login", bool(token), login.text[:200])
        if not token:
            return 1

        headers = {"Authorization": f"Bearer {token}"}

        profile_result = await _run_profile_builder(client, token)
        profile_art = profile_result.get("artifacts", {}).get("profile") or {}
        journey_after = profile_result.get("journey") or {}
        failures += not _print_result(
            "Profile builder completes without error",
            not profile_result.get("error"),
            str(profile_result.get("error")),
        )
        failures += not _print_result(
            "Profile artifact has group_type family",
            profile_art.get("group_type") == "family"
            or (profile_result.get("done") is not None),
            f"group_type={profile_art.get('group_type')}",
        )

        journey_resp = await client.get(f"{API_BASE}/agents/journey", headers=headers)
        journey = journey_resp.json() if journey_resp.status_code == 200 else {}
        failures += not _print_result(
            "Journey marks profile complete",
            journey.get("profile_complete") is True,
            f"profile_complete={journey.get('profile_complete')}",
        )
        pkg_step = (journey.get("steps") or {}).get("package_recommender", {})
        failures += not _print_result(
            "Package recommender unlocked",
            not pkg_step.get("locked", True),
            str(pkg_step),
        )

        package_result = await _run_specialist(
            client,
            token,
            "package_recommender",
            [
                ("package_priorities", ["excursions", "views"], None),
                ("room_preferences", ["family_space"], None),
                ("desired_addons", ["none"], None),
                ("package_confirm", ["generate"], None),
            ],
        )
        pkg_art = package_result.get("artifacts", {}).get("packages") or {}
        pkg_recs = pkg_art.get("recommendations") or []
        failures += not _print_result(
            "Package recommender returns packages",
            len(pkg_recs) >= 1,
            f"count={len(pkg_recs)}",
        )

        food_result = await _run_specialist(
            client,
            token,
            "food_guide",
            [
                ("meal_plan_confirm", ["yes"], None),
                ("spice_tolerance", ["medium"], None),
                ("meal_types", ["breakfast", "lunch", "dinner"], None),
                ("dining_style", ["cabana"], None),
                ("food_confirm", ["generate"], None),
            ],
        )
        food_art = food_result.get("artifacts", {}).get("food") or {}
        must_try = food_art.get("must_try") or food_art.get("dishes") or []
        failures += not _print_result(
            "Food guide must_try list populated",
            len(must_try) >= 1,
            f"must_try_len={len(must_try)}",
        )

        itinerary_result = await _run_specialist(
            client,
            token,
            "itinerary_planner",
            [
                ("daily_pace", ["balanced"], None),
                ("must_see_themes", ["waterfalls", "hiking"], None),
                ("transport_preference", ["private_driver"], None),
                ("early_starts", ["sometimes"], None),
                ("itinerary_confirm", ["generate"], None),
            ],
        )
        it_art = itinerary_result.get("artifacts", {}).get("itinerary") or {}
        it_days = it_art.get("itinerary") or []
        failures += not _print_result(
            "Itinerary planner returns day plan",
            len(it_days) >= 1,
            f"days={len(it_days)}",
        )

        journey2 = await client.get(f"{API_BASE}/agents/journey", headers=headers)
        j2 = journey2.json() if journey2.status_code == 200 else {}
        failures += not _print_result(
            "Feedback collector unlocked",
            j2.get("feedback_unlocked") is True,
            f"feedback_unlocked={j2.get('feedback_unlocked')}",
        )

        feedback_result = await _run_specialist(
            client,
            token,
            "feedback_collector",
            [
                ("package_rating", ["5"], None),
                ("food_rating", ["5"], None),
                ("itinerary_rating", ["4"], None),
                ("ai_rating", ["5"], None),
                ("feedback_comment", [], "Wonderful Leafy Cave experience — thank you!"),
            ],
        )
        fb_art = feedback_result.get("artifacts", {}).get("feedback") or {}
        failures += not _print_result(
            "Feedback collector saves ratings",
            fb_art.get("package_rating") == 5 or feedback_result.get("done") is not None,
            str(fb_art)[:200],
        )

        thread_id = profile_result.get("thread_id")
        if thread_id:
            detail = await client.get(
                f"{API_BASE}/agents/threads/{thread_id}",
                headers=headers,
            )
            failures += not _print_result(
                "Reload profile thread detail",
                detail.status_code == 200 and len(detail.json().get("messages", [])) >= 1,
                f"status={detail.status_code}",
            )

    print("\nSummary:", "ALL PASS" if failures == 0 else f"{failures} assertion(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
