"""Password reset token generation and validation."""

import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.password_reset_token import PasswordResetToken
from models.user import User

logger = logging.getLogger(__name__)

RESET_TOKEN_BYTES = 32
RESET_TOKEN_TTL_HOURS = 1


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def create_password_reset_token(db: AsyncSession, user: User) -> str:
    """Create a reset token, persist its hash, and return the plaintext token."""
    raw_token = secrets.token_urlsafe(RESET_TOKEN_BYTES)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_TTL_HOURS)

    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
    )
    await db.flush()

    logger.warning(
        "Password reset token generated for user_id=%s (MVP: email not sent). token=%s",
        user.id,
        raw_token,
    )
    return raw_token


async def consume_password_reset_token(
    db: AsyncSession,
    raw_token: str,
) -> User | None:
    """Validate reset token and return the associated user, or None if invalid."""
    token_hash = _hash_token(raw_token.strip())
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        return None

    user_result = await db.execute(select(User).where(User.id == record.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        return None

    record.used_at = now
    await db.flush()
    return user
