"""Aggregate Agent Hub outputs into a single trip pack for PDF and email."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified

from agents.profile_builder import ProfileBuilderAgent
from models.agent_thread import AgentThread
from models.enums import SessionStatus
from models.session import Session
from models.user import User
from services.guest_profile_seed import seed_guest_profile
from services.journey_service import (
    OPTIONAL_AGENT_IDS,
    _optional_artifacts_complete,
    _planning_block,
    _profile_from_threads,
)

TRIP_PACK_EMAIL_SENT_KEY = "_trip_pack_email_sent"
TRIP_PACK_EMAIL_SENT_AT_KEY = "_trip_pack_email_sent_at"


class TripSummaryService:
    """Build trip pack JSON from hub agent threads and guest profile."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def load_threads(self, user_id: uuid.UUID) -> list[AgentThread]:
        result = await self._db.execute(
            select(AgentThread)
            .where(AgentThread.user_id == user_id)
            .options(selectinload(AgentThread.messages))
            .order_by(AgentThread.updated_at.desc())
        )
        return list(result.scalars().all())

    def _latest_thread_by_agent(self, threads: list[AgentThread]) -> dict[str, AgentThread]:
        by_agent: dict[str, AgentThread] = {}
        for thread in threads:
            if thread.agent_id not in by_agent:
                by_agent[thread.agent_id] = thread
        return by_agent

    async def build_summary(self, user_id: uuid.UUID) -> dict[str, Any]:
        """Full trip pack payload for API, PDF, and preview."""
        seeded = await seed_guest_profile(self._db, user_id)
        threads = await self.load_threads(user_id)
        by_agent = self._latest_thread_by_agent(threads)

        profile = _profile_from_threads(threads, seeded)
        packages_block = self._packages_from_thread(by_agent.get("package_recommender"))
        food_block = self._food_from_thread(by_agent.get("food_guide"))
        itinerary_block = self._itinerary_from_thread(by_agent.get("itinerary_planner"))

        planners_done: dict[str, bool] = {}
        for agent_id in OPTIONAL_AGENT_IDS:
            thread = by_agent.get(agent_id)
            artifacts = thread.get_artifacts() if thread else {}
            planners_done[agent_id] = _optional_artifacts_complete(agent_id, artifacts)

        trip_pack_ready = all(planners_done.values())
        email_sent = bool(profile.get(TRIP_PACK_EMAIL_SENT_KEY))

        user_row = await self._db.get(User, user_id)
        display = self._guest_display_name(profile, user_row)

        return {
            "profile": profile,
            "profile_complete": ProfileBuilderAgent.is_profile_complete(profile),
            "packages": packages_block,
            "food": food_block,
            "itinerary": itinerary_block,
            "planners_done": planners_done,
            "trip_pack_ready": trip_pack_ready,
            "trip_pack_email_sent": email_sent,
            "guest_email": (profile.get("email") or "").strip() or None,
            "guest_name": display,
        }

    @staticmethod
    def _guest_display_name(profile: dict[str, Any], user: User | None) -> str:
        name = (profile.get("full_name") or "").strip()
        if not name and user and user.full_name:
            name = user.full_name.strip()
        if name:
            return name.split()[0]
        return "Valued Guest"

    @staticmethod
    def _packages_from_thread(thread: AgentThread | None) -> dict[str, Any]:
        if not thread:
            return {"recommendations": [], "narrative": ""}
        block = _planning_block("package_recommender", thread.get_artifacts())
        return {
            "recommendations": block.get("recommendations") or [],
            "narrative": block.get("narrative") or "",
        }

    @staticmethod
    def _food_from_thread(thread: AgentThread | None) -> dict[str, Any]:
        if not thread:
            return {"must_try": [], "safe_starter": None, "dishes_to_avoid": [], "narrative": ""}
        block = _planning_block("food_guide", thread.get_artifacts())
        # Fallback: parse from last assistant message artifacts
        if not block.get("must_try") and thread.messages:
            for msg in sorted(thread.messages, key=lambda m: m.created_at or 0, reverse=True):
                if msg.role == "assistant" and msg.artifacts:
                    alt = msg.artifacts.get("food") or msg.artifacts
                    if alt.get("must_try"):
                        block = alt
                        break
        return {
            "must_try": block.get("must_try") or [],
            "safe_starter": block.get("safe_starter"),
            "dishes_to_avoid": block.get("dishes_to_avoid") or [],
            "narrative": block.get("narrative") or "",
        }

    @staticmethod
    def _itinerary_from_thread(thread: AgentThread | None) -> dict[str, Any]:
        if not thread:
            return {"itinerary": [], "narrative": "", "total_estimated_cost_usd": 0}
        block = _planning_block("itinerary_planner", thread.get_artifacts())
        if not block.get("itinerary") and thread.messages:
            for msg in sorted(thread.messages, key=lambda m: m.created_at or 0, reverse=True):
                if msg.role == "assistant" and msg.artifacts:
                    alt = msg.artifacts.get("itinerary") or msg.artifacts
                    days = alt.get("itinerary") if isinstance(alt, dict) else alt
                    if days:
                        block = alt if isinstance(alt, dict) else {"itinerary": days}
                        break
        return {
            "itinerary": block.get("itinerary") or [],
            "narrative": block.get("narrative") or "",
            "total_estimated_cost_usd": block.get("total_estimated_cost_usd", 0),
            "curated_count": block.get("curated_count", 0),
            "discovered_count": block.get("discovered_count", 0),
        }

    async def mark_email_sent(self, user: User, profile: dict[str, Any]) -> None:
        """Record trip pack email sent on profile (profile builder thread + active session)."""
        from datetime import datetime, timezone

        profile = dict(profile)
        profile[TRIP_PACK_EMAIL_SENT_KEY] = True
        profile[TRIP_PACK_EMAIL_SENT_AT_KEY] = datetime.now(timezone.utc).isoformat()

        result = await self._db.execute(
            select(AgentThread).where(
                AgentThread.user_id == user.id,
                AgentThread.agent_id == "profile_builder",
            )
        )
        pb_thread = result.scalar_one_or_none()
        if pb_thread:
            gp = pb_thread.get_guest_profile()
            gp.update({k: v for k, v in profile.items() if not str(k).startswith("_last_")})
            pb_thread.set_guest_profile(gp)

        session_result = await self._db.execute(
            select(Session)
            .where(Session.user_id == user.id, Session.status == SessionStatus.ACTIVE)
            .order_by(Session.updated_at.desc())
            .limit(1)
        )
        session = session_result.scalar_one_or_none()
        if session:
            gp = session.get_guest_profile()
            gp[TRIP_PACK_EMAIL_SENT_KEY] = True
            gp[TRIP_PACK_EMAIL_SENT_AT_KEY] = profile[TRIP_PACK_EMAIL_SENT_AT_KEY]
            session.guest_profile = gp
            flag_modified(session, "guest_profile")

        await self._db.flush()
