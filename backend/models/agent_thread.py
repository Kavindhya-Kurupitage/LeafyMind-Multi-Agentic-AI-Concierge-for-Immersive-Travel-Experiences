"""Per-agent conversation thread ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, func, select
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.enums import AgentThreadStatus, pg_enum

if TYPE_CHECKING:
    from models.agent_message import AgentMessage
    from models.user import User


class AgentThread(Base):
    """Isolated conversation thread for a single specialist agent."""

    __tablename__ = "agent_threads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New conversation")
    status: Mapped[AgentThreadStatus] = mapped_column(
        pg_enum(AgentThreadStatus, "agent_thread_status"),
        nullable=False,
        default=AgentThreadStatus.ACTIVE,
    )
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="agent_threads")
    messages: Mapped[list["AgentMessage"]] = relationship(
        back_populates="thread",
        order_by="AgentMessage.created_at",
        cascade="all, delete-orphan",
    )

    def get_guest_profile(self) -> dict[str, Any]:
        """Return guest profile stored on this thread's context."""
        return dict((self.context or {}).get("guest_profile") or {})

    def set_guest_profile(self, profile: dict[str, Any]) -> None:
        """Persist guest profile on thread context."""
        ctx = dict(self.context or {})
        ctx["guest_profile"] = profile
        self.context = ctx

    def get_artifacts(self) -> dict[str, Any]:
        """Return latest structured artifacts for this thread."""
        return dict((self.context or {}).get("artifacts") or {})

    def set_artifacts(self, artifacts: dict[str, Any]) -> None:
        """Persist structured agent outputs on thread context."""
        ctx = dict(self.context or {})
        ctx["artifacts"] = artifacts
        self.context = ctx

    def get_agent_preferences(self) -> dict[str, Any]:
        """Return specialist-specific preferences gathered before generation."""
        return dict((self.context or {}).get("agent_preferences") or {})

    def set_agent_preferences(self, preferences: dict[str, Any]) -> None:
        """Persist specialist-specific preferences on thread context."""
        ctx = dict(self.context or {})
        ctx["agent_preferences"] = preferences
        self.context = ctx

    def get_interview_phase(self) -> str:
        """Return discovery | generate for planning specialists."""
        return str((self.context or {}).get("interview_phase") or "discovery")

    def set_interview_phase(self, phase: str) -> None:
        """Set interview phase on thread context."""
        ctx = dict(self.context or {})
        ctx["interview_phase"] = phase
        self.context = ctx

    @classmethod
    async def list_for_user(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        agent_id: str | None = None,
        limit: int = 50,
    ) -> list["AgentThread"]:
        """List threads for a user, optionally filtered by agent."""
        query = select(cls).where(cls.user_id == user_id).order_by(cls.updated_at.desc()).limit(limit)
        if agent_id:
            query = query.where(cls.agent_id == agent_id)
        result = await db.execute(query)
        return list(result.scalars().all())
