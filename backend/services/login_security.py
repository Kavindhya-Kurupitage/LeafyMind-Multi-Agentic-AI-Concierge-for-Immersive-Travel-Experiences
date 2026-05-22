"""Login attempt tracking and account lockout."""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.login_attempt import LoginAttempt

LOCKOUT_WINDOW_MINUTES = 15
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MESSAGE = "Too many attempts, try again in 15 minutes"


async def record_login_attempt(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    ip_address: str,
    success: bool,
) -> None:
    """Persist a login attempt."""
    db.add(
        LoginAttempt(
            user_id=user_id,
            ip_address=ip_address[:45],
            success=success,
        )
    )
    await db.flush()


async def is_account_locked(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """True if the user has 5+ failed attempts in the last 15 minutes."""
    since = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    result = await db.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.user_id == user_id,
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= since,
        )
    )
    failed_count = result.scalar() or 0
    return failed_count >= MAX_FAILED_ATTEMPTS
