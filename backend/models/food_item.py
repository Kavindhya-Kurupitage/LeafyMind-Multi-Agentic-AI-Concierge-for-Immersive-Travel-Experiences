"""Sri Lankan food item ORM model for the Food Guide."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base
from models.enums import MealType, SpiceLevel, pg_enum


class FoodItem(Base):
    """Menu or cultural food entry with dietary metadata."""

    __tablename__ = "food_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description_plain_english: Mapped[str | None] = mapped_column(Text)
    ingredients: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    spice_level: Mapped[SpiceLevel] = mapped_column(
        pg_enum(SpiceLevel, "spice_level"),
        nullable=False,
        default=SpiceLevel.MILD,
    )
    dietary_tags: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    allergens: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    cultural_note: Mapped[str | None] = mapped_column(Text)
    meal_type: Mapped[MealType] = mapped_column(
        pg_enum(MealType, "meal_type"),
        nullable=False,
    )
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
