"""PostgreSQL-aligned Python enums for LeafyMind ORM models."""

import enum

from sqlalchemy import Enum as SAEnum


def pg_enum(enum_cls: type[enum.Enum], name: str) -> SAEnum:
    """Build a native PostgreSQL enum column that stores member values, not names."""
    return SAEnum(
        enum_cls,
        name=name,
        create_constraint=False,
        native_enum=True,
        values_callable=lambda cls: [member.value for member in cls],
    )


class UserRole(str, enum.Enum):
    GUEST = "guest"
    OWNER = "owner"
    ADMIN = "admin"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class AgentThreadStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class PackageTier(str, enum.Enum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"


class AttractionCategory(str, enum.Enum):
    WILDLIFE = "wildlife"
    WATERFALL = "waterfall"
    TEMPLE = "temple"
    HIKING = "hiking"
    BEACH = "beach"
    CULTURAL = "cultural"
    FOOD_EXPERIENCE = "food_experience"


class FitnessLevel(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class SpiceLevel(str, enum.Enum):
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"
