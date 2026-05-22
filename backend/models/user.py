"""User account ORM model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Self

from passlib.context import CryptContext
from sqlalchemy import DateTime, String, func, select
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from models.enums import UserRole, pg_enum

if TYPE_CHECKING:
    from models.agent_thread import AgentThread
    from models.feedback import Feedback
    from models.session import Session

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    """Registered guest, owner, or admin user."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"),
        nullable=False,
        default=UserRole.GUEST,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    agent_threads: Mapped[list["AgentThread"]] = relationship(back_populates="user")
    feedback_entries: Mapped[list["Feedback"]] = relationship(back_populates="user")

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hash a plain-text password with bcrypt."""
        return pwd_context.hash(plain_password)

    @classmethod
    def create_user(
        cls,
        email: str,
        password: str,
        full_name: str | None = None,
        role: UserRole = UserRole.GUEST,
    ) -> Self:
        """Create a User instance with a bcrypt-hashed password (not yet persisted)."""
        return cls(
            email=email.strip().lower(),
            password_hash=cls.hash_password(password),
            full_name=full_name,
            role=role,
        )

    def verify_password(self, plain_password: str) -> bool:
        """Return True if the plain password matches the stored bcrypt hash."""
        return pwd_context.verify(plain_password, self.password_hash)

    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Self | None:
        """Fetch a user by email address."""
        result = await db.execute(select(cls).where(cls.email == email.strip().lower()))
        return result.scalar_one_or_none()
