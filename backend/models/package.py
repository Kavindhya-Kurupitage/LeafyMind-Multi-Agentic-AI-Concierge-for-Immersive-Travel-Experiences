"""Stay package ORM model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.enums import PackageTier, pg_enum


class Package(Base):
    """Leafy Cave accommodation or experience package."""

    __tablename__ = "packages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[PackageTier] = mapped_column(
        pg_enum(PackageTier, "package_tier"),
        nullable=False,
    )
    price_per_night_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    description: Mapped[str | None] = mapped_column(Text)
    inclusions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    exclusions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    travel_styles: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    group_types: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    min_nights: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    max_guests: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    seasonal_note: Mapped[str | None] = mapped_column(Text)
    package_meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
