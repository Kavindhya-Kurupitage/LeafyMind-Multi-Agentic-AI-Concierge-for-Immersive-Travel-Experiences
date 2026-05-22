"""Load guest profile from Profile Builder threads, sessions, or other hub threads."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.profile_builder import ProfileBuilderAgent
from models.agent_thread import AgentThread
from models.session import Session


def _clean_profile(raw: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


async def seed_guest_profile(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """
    Prefer the richest profile from Profile Builder, then other hub threads,
    then the latest concierge session.
    """
    profile: dict[str, Any] = {}

    pb_result = await db.execute(
        select(AgentThread)
        .where(
            AgentThread.user_id == user_id,
            AgentThread.agent_id == "profile_builder",
        )
        .order_by(AgentThread.updated_at.desc())
        .limit(3)
    )
    for thread in pb_result.scalars().all():
        candidate = _clean_profile(thread.get_guest_profile())
        if len(candidate) > len(profile):
            profile = candidate
        artifacts = thread.get_artifacts()
        if artifacts.get("profile"):
            nested = artifacts["profile"]
            if isinstance(nested, dict) and "profile" in nested:
                candidate = _clean_profile(nested["profile"])
            else:
                candidate = _clean_profile(nested)
            if len(candidate) > len(profile):
                profile = candidate

    if not ProfileBuilderAgent.is_profile_complete(profile):
        other_result = await db.execute(
            select(AgentThread)
            .where(AgentThread.user_id == user_id)
            .order_by(AgentThread.updated_at.desc())
            .limit(10)
        )
        for thread in other_result.scalars().all():
            candidate = _clean_profile(thread.get_guest_profile())
            if len(candidate) > len(profile):
                profile = candidate

    session_result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.updated_at.desc())
        .limit(1)
    )
    session = session_result.scalar_one_or_none()
    if session:
        candidate = _clean_profile(session.get_guest_profile())
        if len(candidate) > len(profile):
            profile = candidate

    return profile
