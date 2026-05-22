"""Authentication routes — register, login, profile, logout, and password reset."""

import asyncio
import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from services.auth_service import (
    INVALID_CREDENTIALS_MSG,
    build_token_for_user,
    get_current_user,
    get_token_payload,
    revoke_token,
)
from services.login_security import (
    LOCKOUT_MESSAGE,
    is_account_locked,
    record_login_attempt,
)
from services.password_reset_service import (
    consume_password_reset_token,
    create_password_reset_token,
)

router = APIRouter()

PASSWORD_PATTERN_UPPER = re.compile(r"[A-Z]")
PASSWORD_PATTERN_DIGIT = re.compile(r"\d")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()[:45]
    if request.client and request.client.host:
        return request.client.host[:45]
    return "unknown"


def _validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not PASSWORD_PATTERN_UPPER.search(value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not PASSWORD_PATTERN_DIGIT.search(value):
        raise ValueError("Password must contain at least one number")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class PasswordResetRequestBody(BaseModel):
    email: EmailStr


class PasswordResetConfirmBody(BaseModel):
    token: str = Field(..., min_length=16, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserPublic(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str

    model_config = {"from_attributes": True}

    @classmethod
    def from_user(cls, user: User) -> "UserPublic":
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
        )


class RegisterResponse(BaseModel):
    message: str
    user_id: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class LogoutResponse(BaseModel):
    message: str


class MessageResponse(BaseModel):
    message: str


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterResponse:
    """Register a new guest account."""
    existing = await User.get_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = await asyncio.to_thread(
        User.create_user,
        body.email,
        body.password,
        body.full_name,
    )
    db.add(user)
    await db.flush()

    return RegisterResponse(
        message="Account created successfully",
        user_id=str(user.id),
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """Authenticate and return a JWT access token."""
    ip_address = _client_ip(request)
    user = await User.get_by_email(db, body.email)

    if user is not None and await is_account_locked(db, user.id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=LOCKOUT_MESSAGE,
        )

    success = user is not None and await asyncio.to_thread(
        user.verify_password, body.password
    )

    if user is not None:
        await record_login_attempt(
            db, user_id=user.id, ip_address=ip_address, success=success
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MSG,
        )

    access_token, expires_in = build_token_for_user(user)
    return LoginResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=UserPublic.from_user(user),
    )


@router.get("/me", response_model=UserPublic)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserPublic:
    """Return the authenticated user's profile."""
    return UserPublic.from_user(current_user)


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    token_payload: Annotated[dict, Depends(get_token_payload)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LogoutResponse:
    """Revoke the current JWT so it cannot be reused."""
    await revoke_token(db, token_payload["jti"], reason="logout")
    return LogoutResponse(message="Logged out successfully")


@router.post("/password-reset-request", response_model=MessageResponse)
async def password_reset_request(
    body: PasswordResetRequestBody,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Request a password reset link (same response whether or not the email exists)."""
    user = await User.get_by_email(db, body.email)
    if user is not None:
        await create_password_reset_token(db, user)

    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent.",
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def password_reset_confirm(
    body: PasswordResetConfirmBody,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """Validate reset token and set a new password."""
    user = await consume_password_reset_token(db, body.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user.password_hash = User.hash_password(body.new_password)
    await db.flush()

    return MessageResponse(message="Password updated successfully. You can sign in now.")
