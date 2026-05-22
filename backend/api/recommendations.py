"""Recommendation API — structured package and itinerary data from sessions."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.session_access import get_session_for_user
from database import get_db
from models.user import User

router = APIRouter()


@router.get("/packages/{session_id}")
async def get_package_recommendations(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the last package recommendations stored for this session."""
    session = await get_session_for_user(db, session_id, user)
    profile = session.get_guest_profile()
    recommendations = profile.get("_last_package_recommendations")

    if not recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No package recommendations available for this session yet",
        )

    return {
        "session_id": str(session.id),
        "phase": session.get_phase(),
        "recommendations": recommendations,
        "guest_profile": {
            k: v
            for k, v in profile.items()
            if not str(k).startswith("_")
        },
    }


@router.get("/food/{session_id}")
async def get_food_guide(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the last food guide stored for this session."""
    session = await get_session_for_user(db, session_id, user)
    profile = session.get_guest_profile()
    food_data = profile.get("_last_food_guide")

    if not food_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No food guide available for this session yet",
        )

    return {
        "session_id": str(session.id),
        "phase": session.get_phase(),
        **food_data,
    }


@router.get("/itinerary/{session_id}")
async def get_itinerary(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return the last generated itinerary for this session."""
    session = await get_session_for_user(db, session_id, user)
    profile = session.get_guest_profile()
    itinerary_data = profile.get("_last_itinerary")

    if not itinerary_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No itinerary available for this session yet",
        )

    return {
        "session_id": str(session.id),
        "phase": session.get_phase(),
        **itinerary_data,
    }
