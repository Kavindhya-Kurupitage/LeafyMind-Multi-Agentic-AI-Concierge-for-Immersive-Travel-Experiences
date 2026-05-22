"""Local attraction ORM model."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.enums import AttractionCategory, FitnessLevel, pg_enum


class Attraction(Base):
    """Cultural site, beach, or activity near Leafy Cave."""

    __tablename__ = "attractions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[AttractionCategory] = mapped_column(
        pg_enum(AttractionCategory, "attraction_category"),
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(Text)
    distance_km_from_cabana: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    estimated_duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    entry_fee_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fitness_level_required: Mapped[FitnessLevel] = mapped_column(
        pg_enum(FitnessLevel, "fitness_level"),
        nullable=False,
        default=FitnessLevel.LOW,
    )
    suitable_for: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    seasonal_availability: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    tips: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
