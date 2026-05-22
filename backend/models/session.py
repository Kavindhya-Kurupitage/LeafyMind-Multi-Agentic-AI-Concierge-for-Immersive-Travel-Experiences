"""Concierge session ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import flag_modified

from database import Base
from models.enums import SessionStatus, pg_enum
from models.guest_profile import GuestProfile

if TYPE_CHECKING:
    from models.escalation import Escalation
    from models.feedback import Feedback
    from models.user import User

PHASE_KEY = "_phase"
VALID_PHASES = frozenset(
    {
        "GREETING",
        "PROFILING",
        "CONTACT_COLLECTION",
        "RECOMMENDING",
        "ITINERARY",
        "FOLLOWUP",
        "FEEDBACK",
        "ESCALATED",
    }
)


class Session(Base):
    """Guest concierge chat session with embedded profile and history."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # JSONB — shape defined by models.guest_profile.GuestProfile (includes optional email, whatsapp_number)
    guest_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    conversation_history: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    status: Mapped[SessionStatus] = mapped_column(
        pg_enum(SessionStatus, "session_status"),
        nullable=False,
        default=SessionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    feedback_email_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    feedback_email_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="sessions")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="session")
    escalations: Mapped[list["Escalation"]] = relationship(back_populates="session")

    def get_conversation_history(self) -> list[dict[str, Any]]:
        """Return the full conversation history as a list of turn dicts."""
        return list(self.conversation_history or [])

    def append_turn(self, role: str, content: str, agent_used: str | None = None) -> None:
        """Append a single conversation turn and mark the column dirty for SQLAlchemy."""
        history = self.get_conversation_history()
        turn: dict[str, Any] = {"role": role, "content": content}
        if agent_used:
            turn["agent_used"] = agent_used
        history.append(turn)
        self.conversation_history = history
        flag_modified(self, "conversation_history")

    def get_guest_profile(self) -> dict[str, Any]:
        """Return raw guest profile dict (includes internal keys like _phase)."""
        return dict(self.guest_profile or {})

    def get_guest_profile_model(self) -> GuestProfile:
        """Return guest profile as a validated GuestProfile model."""
        return GuestProfile.from_dict(self.get_guest_profile())

    def update_guest_profile(self, fields: dict[str, Any]) -> None:
        """Merge fields into guest_profile JSONB."""
        profile = self.get_guest_profile()
        profile.update(fields)
        self.guest_profile = profile
        flag_modified(self, "guest_profile")

    def get_phase(self) -> str:
        """Return the current concierge phase (defaults to GREETING)."""
        return str(self.get_guest_profile().get(PHASE_KEY, "GREETING"))

    def set_phase(self, phase: str) -> None:
        """Set the concierge phase on the session."""
        if phase not in VALID_PHASES:
            raise ValueError(f"Invalid phase: {phase}. Must be one of {sorted(VALID_PHASES)}")
        self.update_guest_profile({PHASE_KEY: phase})
