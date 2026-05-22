"""Shared helpers for chat session access control."""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import SessionStatus
from models.session import Session
from models.user import User
from services.prompt_sanitizer import sanitize_user_input

MAX_MESSAGE_LENGTH = 2000


def sanitize_message(text: str) -> str:
    """Strip HTML/injection patterns and cap message length."""
    return sanitize_user_input(text or "")[:MAX_MESSAGE_LENGTH]


async def create_new_session(db: AsyncSession, user: User) -> Session:
    """Create a fresh concierge session for the authenticated user."""
    session = Session(
        user_id=user.id,
        session_token=secrets.token_urlsafe(32),
        guest_profile={"_phase": "GREETING"},
        conversation_history=[],
        status=SessionStatus.ACTIVE,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(session)
    await db.flush()
    return session


async def get_session_for_user(
    db: AsyncSession,
    session_id: uuid.UUID,
    user: User,
) -> Session:
    """Load a session and verify ownership; raise 404/403 otherwise."""
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this session",
        )
    return session
