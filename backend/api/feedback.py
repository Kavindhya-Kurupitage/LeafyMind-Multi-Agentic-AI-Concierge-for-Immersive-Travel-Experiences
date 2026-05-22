"""Feedback API — guest submissions and owner dashboard."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from api.session_access import get_session_for_user
from database import get_db
from models.enums import UserRole
from models.feedback import Feedback
from models.user import User
from services.auth_service import require_role
from services.owner_analytics import _feedback_to_dict, get_owner_dashboard_summary

router = APIRouter()


class FeedbackSubmitRequest(BaseModel):
    """Structured feedback submission body."""

    session_id: uuid.UUID
    package_rating: int | None = Field(None, ge=1, le=5)
    food_rating: int | None = Field(None, ge=1, le=5)
    itinerary_rating: int | None = Field(None, ge=1, le=5)
    ai_helpfulness_rating: int | None = Field(None, ge=1, le=5)
    free_text_feedback: str | None = Field(None, max_length=4000)


class FeedbackSubmitResponse(BaseModel):
    id: str
    message: str
    flagged_for_review: bool = False


class FeedbackFlagResponse(BaseModel):
    id: str
    flagged_for_review: bool


class OwnerSummaryResponse(BaseModel):
    total_sessions_week: int
    active_sessions: int
    flagged_count: int
    most_recommended_package: str | None
    avg_ratings: dict[str, float]
    recent_feedback: list[dict[str, Any]]


@router.post("/submit", response_model=FeedbackSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    body: FeedbackSubmitRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> FeedbackSubmitResponse:
    """Accept a feedback record and persist it to PostgreSQL."""
    await get_session_for_user(db, body.session_id, user)

    auto_tags: list[str] = []
    if all(
        (getattr(body, f"{k}_rating") or 0) >= 4
        for k in ("package", "food", "itinerary", "ai_helpfulness")
        if getattr(body, f"{k}_rating") is not None
    ):
        auto_tags.append("positive")
    if (body.package_rating or 5) <= 2:
        auto_tags.append("value_complaint")
    if (body.food_rating or 5) <= 2:
        auto_tags.append("food_issue")
    if (body.itinerary_rating or 5) <= 2:
        auto_tags.append("itinerary_mismatch")
    if (body.ai_helpfulness_rating or 0) >= 4:
        auto_tags.append("ai_helpful")
    elif body.ai_helpfulness_rating is not None:
        auto_tags.append("ai_unhelpful")

    flagged = (
        (body.package_rating or 5) <= 2
        or (body.food_rating or 5) <= 2
        or (body.itinerary_rating or 5) <= 2
        or (body.ai_helpfulness_rating or 5) <= 2
    )

    record = Feedback(
        session_id=body.session_id,
        user_id=user.id,
        package_rating=body.package_rating,
        food_rating=body.food_rating,
        itinerary_rating=body.itinerary_rating,
        ai_helpfulness_rating=body.ai_helpfulness_rating,
        free_text_feedback=body.free_text_feedback,
        auto_tags=auto_tags or ["positive"],
        flagged_for_review=flagged,
    )
    db.add(record)
    await db.flush()

    return FeedbackSubmitResponse(
        id=str(record.id),
        message="Thank you — your feedback means a great deal to everyone at Leafy Cave.",
        flagged_for_review=flagged,
    )


@router.get("/summary", response_model=OwnerSummaryResponse)
async def feedback_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    _owner: Annotated[User, Depends(require_role(UserRole.OWNER))],
) -> OwnerSummaryResponse:
    """Owner dashboard summary — sessions, ratings, flagged count, recommendations."""
    data = await get_owner_dashboard_summary(db)
    return OwnerSummaryResponse(**data)


@router.get("/flagged")
async def feedback_flagged(
    db: Annotated[AsyncSession, Depends(get_db)],
    _owner: Annotated[User, Depends(require_role(UserRole.OWNER))],
) -> dict[str, Any]:
    """Return all feedback records flagged for owner review."""
    result = await db.execute(
        select(Feedback)
        .where(Feedback.flagged_for_review.is_(True))
        .order_by(Feedback.created_at.desc())
    )
    items = result.scalars().all()
    return {
        "count": len(items),
        "items": [_feedback_to_dict(f) for f in items],
    }


@router.post("/flag/{feedback_id}", response_model=FeedbackFlagResponse)
async def toggle_feedback_flag(
    feedback_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _owner: Annotated[User, Depends(require_role(UserRole.OWNER))],
) -> FeedbackFlagResponse:
    """Toggle flagged_for_review on a feedback record (owner only)."""
    result = await db.execute(select(Feedback).where(Feedback.id == feedback_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found")

    record.flagged_for_review = not record.flagged_for_review
    await db.flush()

    return FeedbackFlagResponse(
        id=str(record.id),
        flagged_for_review=record.flagged_for_review,
    )
