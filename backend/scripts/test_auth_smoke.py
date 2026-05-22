"""
Phases 1–2 API smoke tests: health endpoints, register, login, wrong password, journey auth.

Run inside Docker (backend can reach itself on port 8000):

    docker exec leafymind-backend python -m scripts.test_auth_smoke

Optional env:
    INTEGRATION_API_BASE — default http://127.0.0.1:8000
    BFF_HEALTH_URL — default http://host.docker.internal:3002/health
    FRONTEND_URL — default http://host.docker.internal:5174
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path

import httpx
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

load_dotenv(REPO_ROOT / ".env")

API_BASE = os.getenv("INTEGRATION_API_BASE", "http://127.0.0.1:8000").rstrip("/")
BFF_HEALTH = os.getenv(
    "BFF_HEALTH_URL",
    os.getenv("INTEGRATION_BFF_HEALTH", "http://bff:3001/health"),
)
FRONTEND_URL = os.getenv(
    "INTEGRATION_FRONTEND_URL",
    os.getenv("FRONTEND_INTERNAL_URL", "http://frontend:5173"),
).rstrip("/")

TEST_EMAIL = os.getenv("TEST_GUEST_EMAIL", "guest.test1@example.com")
TEST_PASSWORD = os.getenv("TEST_GUEST_PASSWORD", "TestGuest1")
TEST_NAME = os.getenv("TEST_GUEST_NAME", "Guest A Tester")


def _print_result(name: str, ok: bool, detail: str = "") -> bool:
    label = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"[{label}] {name}{suffix}")
    return ok


async def main() -> int:
    failures = 0

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
        backend_health = await client.get(f"{API_BASE}/health")
        failures += not _print_result(
            "Backend GET /health",
            backend_health.status_code == 200,
            backend_health.text[:120],
        )

        try:
            bff_health = await client.get(BFF_HEALTH)
            bff_ok = bff_health.status_code == 200
            bff_detail = bff_health.text[:120]
        except httpx.RequestError as exc:
            bff_ok = False
            bff_detail = str(exc)
        failures += not _print_result("BFF GET /health", bff_ok, bff_detail)

        try:
            landing = await client.get(
                FRONTEND_URL,
                headers={"Host": "localhost"},
            )
            landing_ok = landing.status_code == 200 and (
                "leafy" in landing.text.lower()
                or "vite" in landing.text.lower()
                or "<!doctype html" in landing.text.lower()[:200]
            )
            landing_detail = f"status={landing.status_code}"
        except httpx.RequestError as exc:
            landing_ok = False
            landing_detail = str(exc)
        failures += not _print_result("Frontend landing page loads", landing_ok, landing_detail)

        reg = await client.post(
            f"{API_BASE}/auth/register",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD,
                "full_name": TEST_NAME,
            },
        )
        reg_ok = reg.status_code == 201 or (
            reg.status_code == 400 and "already" in reg.text.lower()
        )
        failures += not _print_result(
            "Register Guest A (201 or already exists)",
            reg_ok,
            f"status={reg.status_code}",
        )

        bad_login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": TEST_EMAIL, "password": "WrongPass1"},
        )
        failures += not _print_result(
            "Wrong password rejected",
            bad_login.status_code in (401, 400),
            f"status={bad_login.status_code}",
        )

        login = await client.post(
            f"{API_BASE}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )
        token = login.json().get("access_token") if login.status_code == 200 else None
        failures += not _print_result(
            "Login returns JWT",
            login.status_code == 200 and bool(token),
            login.text[:200],
        )
        if not token:
            print("Aborting — cannot authenticate.")
            return 1

        headers = {"Authorization": f"Bearer {token}"}
        journey = await client.get(f"{API_BASE}/agents/journey", headers=headers)
        failures += not _print_result(
            "Authenticated journey endpoint",
            journey.status_code == 200,
            journey.text[:200],
        )

        no_auth = await client.get(f"{API_BASE}/agents/journey")
        failures += not _print_result(
            "Journey requires auth (401 without token)",
            no_auth.status_code == 401,
            f"status={no_auth.status_code}",
        )

        uid = uuid.uuid4().hex[:8]
        fresh_email = f"smoke_{uid}@example.com"
        fresh_pass = f"Smoke{uid[:4]}1"
        fresh_reg = await client.post(
            f"{API_BASE}/auth/register",
            json={
                "email": fresh_email,
                "password": fresh_pass,
                "full_name": "Smoke User",
            },
        )
        failures += not _print_result(
            "Fresh user registration",
            fresh_reg.status_code == 201,
            f"status={fresh_reg.status_code}",
        )

    print("\nSummary:", "ALL PASS" if failures == 0 else f"{failures} assertion(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
