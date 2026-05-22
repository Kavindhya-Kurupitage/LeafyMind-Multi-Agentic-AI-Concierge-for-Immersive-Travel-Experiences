"""Guest feedback ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from models.session import Session
    from models.user import User


class Feedback(Base):
    """Structured post-session guest feedback."""

    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    package_rating: Mapped[int | None] = mapped_column(Integer)
    food_rating: Mapped[int | None] = mapped_column(Integer)
    itinerary_rating: Mapped[int | None] = mapped_column(Integer)
    ai_helpfulness_rating: Mapped[int | None] = mapped_column(Integer)
    free_text_feedback: Mapped[str | None] = mapped_column(Text)
    auto_tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped["Session"] = relationship(back_populates="feedback_entries")
    user: Mapped["User"] = relationship(back_populates="feedback_entries")
