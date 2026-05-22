"""
Phase 6 integration test — promote guest to owner and verify dashboard APIs.

    docker exec leafymind-backend python -m scripts.test_owner_dashboard
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv
from sqlalchemy import select, update

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(REPO_ROOT / ".env")

import models  # noqa: E402, F401
from database import AsyncSessionLocal, init_db  # noqa: E402
from models.enums import UserRole  # noqa: E402
from models.user import User  # noqa: E402

API_BASE = os.getenv("INTEGRATION_API_BASE", "http://127.0.0.1:8000").rstrip("/")
OWNER_EMAIL = os.getenv("TEST_GUEST_EMAIL", "guest.test1@example.com")
OWNER_PASSWORD = os.getenv("TEST_GUEST_PASSWORD", "TestGuest1")


def _print_result(name: str, ok: bool, detail: str = "") -> bool:
    label = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{label}] {name}{suffix}")
    return ok


async def _promote_to_owner(email: str) -> None:
    await init_db()
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(User).where(User.email == email).values(role=UserRole.OWNER)
        )
        await session.commit()


async def main() -> int:
    failures = 0
    await _promote_to_owner(OWNER_EMAIL)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        guest_email = f"guest_only_{uuid.uuid4().hex[:8]}@example.com"
        guest_pass = "GuestOnly1"
        await client.post(
            f"{API_BASE}/auth/register",
            json={"email": guest_email, "password": guest_pass, "full_name": "Guest Only"},
        )

        owner_login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": OWNER_EMAIL, "password": OWNER_PASSWORD},
        )
        owner_token = owner_login.json().get("access_token")
        failures += not _print_result(
            "Owner login after SQL promote",
            owner_login.status_code == 200 and bool(owner_token),
            owner_login.text[:200],
        )
        if not owner_token:
            return 1

        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        summary = await client.get(f"{API_BASE}/feedback/summary", headers=owner_headers)
        failures += not _print_result(
            "Owner GET /feedback/summary",
            summary.status_code == 200,
            summary.text[:200],
        )
        if summary.status_code == 200:
            body = summary.json()
            failures += not _print_result(
                "Owner summary has session metrics",
                "total_sessions_week" in body,
                str(body.keys()),
            )

        guest_login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": guest_email, "password": guest_pass},
        )
        guest_token = guest_login.json().get("access_token")
        if guest_token:
            guest_headers = {"Authorization": f"Bearer {guest_token}"}
            denied = await client.get(f"{API_BASE}/feedback/summary", headers=guest_headers)
            failures += not _print_result(
                "Guest cannot access owner summary (403)",
                denied.status_code == 403,
                f"status={denied.status_code}",
            )

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == OWNER_EMAIL))
            user = result.scalar_one_or_none()
            failures += not _print_result(
                "User role is owner in database",
                user is not None and user.role == UserRole.OWNER,
                f"role={getattr(user, 'role', None)}",
            )

        if summary.status_code == 200:
            recent = summary.json().get("recent_feedback") or []
            if recent:
                fb_id = recent[0].get("id")
                if fb_id:
                    toggle = await client.post(
                        f"{API_BASE}/feedback/flag/{fb_id}",
                        headers=owner_headers,
                    )
                    failures += not _print_result(
                        "Toggle feedback flag",
                        toggle.status_code == 200,
                        toggle.text[:200],
                    )
                    toggle2 = await client.post(
                        f"{API_BASE}/feedback/flag/{fb_id}",
                        headers=owner_headers,
                    )
                    failures += not _print_result(
                        "Toggle feedback flag again (persist)",
                        toggle2.status_code == 200,
                        toggle2.text[:200],
                    )

    print("\nSummary:", "ALL PASS" if failures == 0 else f"{failures} assertion(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
