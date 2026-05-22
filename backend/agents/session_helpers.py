"""Helpers for loading and creating concierge sessions."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import SessionStatus
from models.session import Session


async def get_or_create_active_session(db: AsyncSession, user_id: uuid.UUID) -> Session:
    """Return the user's active session or create a new one."""
    result = await db.execute(
        select(Session).where(
            Session.user_id == user_id,
            Session.status == SessionStatus.ACTIVE,
        )
    )
    session = result.scalar_one_or_none()
    if session:
        return session

    session = Session(
        user_id=user_id,
        session_token=secrets.token_urlsafe(32),
        guest_profile={"_phase": "GREETING"},
        conversation_history=[],
        status=SessionStatus.ACTIVE,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session)
    await db.flush()
    return session
