"""Shared FastAPI dependencies — re-exported from auth_service for convenience."""

from services.auth_service import (
    create_access_token,
    get_current_user,
    require_role,
    security,
    verify_token,
)

__all__ = [
    "create_access_token",
    "get_current_user",
    "require_role",
    "security",
    "verify_token",
]
