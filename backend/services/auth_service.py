"""Authentication service — JWT tokens and FastAPI security dependencies."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.enums import UserRole
from models.revoked_token import RevokedToken
from models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

INVALID_CREDENTIALS_MSG = "Invalid email or password"
INVALID_TOKEN_MSG = "Invalid or expired token"


def create_access_token(data: dict[str, Any]) -> str:
    """Encode a JWT access token with python-jose."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expiry_minutes)
    payload["exp"] = expire
    if "jti" not in payload:
        payload["jti"] = str(uuid.uuid4())
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and validate a JWT signature/expiry; return payload or None."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        if not payload.get("user_id") or not payload.get("jti"):
            return None
        return payload
    except JWTError:
        return None


async def is_token_revoked(db: AsyncSession, jti: str) -> bool:
    """Return True if the JWT ID has been revoked."""
    result = await db.execute(select(RevokedToken.jti).where(RevokedToken.jti == jti))
    return result.scalar_one_or_none() is not None


async def revoke_token(
    db: AsyncSession,
    jti: str,
    reason: str = "logout",
) -> None:
    """Insert a JWT ID into the revocation table."""
    existing = await db.execute(select(RevokedToken).where(RevokedToken.jti == jti))
    if existing.scalar_one_or_none() is None:
        db.add(RevokedToken(jti=jti, reason=reason))
        await db.flush()


async def verify_token(token: str, db: AsyncSession) -> dict[str, Any] | None:
    """Decode JWT and ensure it has not been revoked."""
    payload = decode_token(token)
    if payload is None:
        return None
    if await is_token_revoked(db, payload["jti"]):
        return None
    return payload


def build_token_for_user(user: User) -> tuple[str, int]:
    """Create a JWT and return (token, expires_in_seconds) for the given user."""
    expires_in = settings.jwt_expiry_minutes * 60
    token = create_access_token(
        {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "jti": str(uuid.uuid4()),
        }
    )
    return token, expires_in


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """FastAPI dependency — resolve the authenticated user from a Bearer JWT."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await verify_token(credentials.credentials, db)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(payload["user_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_token_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Return validated JWT payload (for logout revocation)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = await verify_token(credentials.credentials, db)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_TOKEN_MSG,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_role(*roles: UserRole) -> Callable:
    """Dependency factory that restricts access to users with one of the given roles."""

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_checker
