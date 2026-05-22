"""Link Agent Hub completions to feedback sessions and invitation emails."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import AgentThreadStatus, SessionStatus
from models.session import Session
from models.user import User
from services.email_service import email_service
from services.journey_service import _optional_artifacts_complete, _planning_block
from services.trip_summary_service import TripSummaryService

logger = logging.getLogger(__name__)

OPTIONAL_AGENT_IDS: tuple[str, ...] = (
    "package_recommender",
    "food_guide",
    "itinerary_planner",
)
LAST_OPTIONAL_AGENT_KEY = "_hub_last_optional_agent"


def _package_name_from_profile(profile: dict[str, Any], agent_id: str) -> str:
    artifacts_agent = {
        "package_recommender": "Package planning",
        "food_guide": "Food guide",
        "itinerary_planner": "Itinerary planning",
    }
    recommendations = profile.get("_last_package_recommendations") or []
    if recommendations and isinstance(recommendations[0], dict):
        name = recommendations[0].get("name")
        if name:
            return str(name)
    selected = profile.get("selected_package")
    if selected:
        return str(selected)
    return artifacts_agent.get(agent_id, "your Leafy Cave planning session")


def _guest_display_name(profile: dict[str, Any], user: User) -> str:
    if user.full_name and user.full_name.strip():
        return user.full_name.strip().split()[0]
    return "Valued Guest"


async def get_or_create_hub_feedback_session(
    db: AsyncSession,
    user: User,
    profile: dict[str, Any],
    completed_agent_id: str,
) -> Session:
    """Return an active session used for hub feedback collection and email links."""
    result = await db.execute(
        select(Session)
        .where(
            Session.user_id == user.id,
            Session.status == SessionStatus.ACTIVE,
        )
        .order_by(Session.updated_at.desc())
        .limit(5)
    )
    for session in result.scalars().all():
        profile_data = session.get_guest_profile()
        if profile_data.get(LAST_OPTIONAL_AGENT_KEY):
            clean_profile = {
                k: v
                for k, v in profile.items()
                if not str(k).startswith("_last_")
            }
            clean_profile[LAST_OPTIONAL_AGENT_KEY] = completed_agent_id
            session.guest_profile = {**profile_data, **clean_profile}
            session.set_phase("FEEDBACK")
            return session

    clean_profile = {k: v for k, v in profile.items() if not str(k).startswith("_last_")}
    clean_profile[LAST_OPTIONAL_AGENT_KEY] = completed_agent_id
    session = Session(
        user_id=user.id,
        session_token=secrets.token_urlsafe(32),
        guest_profile={**clean_profile, "_phase": "FEEDBACK"},
        conversation_history=[],
        status=SessionStatus.ACTIVE,
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(session)
    await db.flush()
    return session


async def maybe_complete_optional_agent(
    db: AsyncSession,
    thread: Any,
    user: User,
    artifacts: dict[str, Any],
) -> dict[str, Any] | None:
    """
    When a planning agent finishes, mark the thread complete, ensure a feedback
    session exists, and send the feedback invitation email once.
    """
    agent_id = thread.agent_id
    if agent_id not in OPTIONAL_AGENT_IDS:
        return None

    block = artifacts
    if agent_id == "package_recommender" and not artifacts.get("recommendations"):
        block = _planning_block(agent_id, thread.get_artifacts())
    elif agent_id == "food_guide" and not artifacts.get("must_try"):
        block = _planning_block(agent_id, thread.get_artifacts())
    elif agent_id == "itinerary_planner" and not artifacts.get("itinerary"):
        block = _planning_block(agent_id, thread.get_artifacts())
    if not _optional_artifacts_complete(agent_id, block):
        return None

    if thread.status == AgentThreadStatus.COMPLETED:
        return None

    thread.status = AgentThreadStatus.COMPLETED
    profile = thread.get_guest_profile()

    session = await get_or_create_hub_feedback_session(db, user, profile, agent_id)
    ctx = dict(thread.context or {})
    ctx["feedback_session_id"] = str(session.id)
    thread.context = ctx

    summary = await TripSummaryService(db).build_summary(user.id)
    trip_pack_ready = bool(summary.get("trip_pack_ready"))
    planners_done = summary.get("planners_done") or {}
    planners_done_count = sum(1 for done in planners_done.values() if done)

    email_sent = False
    guest_email = (profile.get("email") or "").strip()
    # Feedback survey email only after all three planners — trip plan PDF is separate (on-demand).
    if trip_pack_ready and guest_email and not session.feedback_email_sent:
        guest_name = _guest_display_name(profile, user)
        stay_summary = {
            "package_name": _package_name_from_profile(profile, agent_id),
            "duration_nights": profile.get("duration_nights", 2),
        }
        email_sent = await email_service.send_feedback_request(
            guest_email,
            guest_name,
            str(session.id),
            stay_summary,
            feedback_path=f"/agents/feedback_collector?session={session.id}",
        )
        if email_sent:
            session.feedback_email_sent = True
            session.feedback_email_sent_at = datetime.now(timezone.utc)

    await db.flush()
    logger.info(
        "Hub planning complete user=%s agent=%s session=%s trip_pack_ready=%s email_sent=%s",
        user.id,
        agent_id,
        session.id,
        trip_pack_ready,
        email_sent,
    )
    return {
        "planning_complete": True,
        "completed_agent": agent_id,
        "feedback_session_id": str(session.id),
        "feedback_email_sent": email_sent or session.feedback_email_sent,
        "trip_pack_ready": trip_pack_ready,
        "planners_done_count": planners_done_count,
        "planners_done": planners_done,
        "open_feedback": trip_pack_ready,
    }
