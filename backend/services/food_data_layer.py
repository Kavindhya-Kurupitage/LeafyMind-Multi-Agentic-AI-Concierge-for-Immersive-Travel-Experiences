"""Single source of truth for food item data queries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.food_item import FoodItem


class FoodDataLayer:
    """Encapsulates all database access for food items."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_available(self, limit: int = 50) -> list[FoodItem]:
        """Return available food items."""
        result = await self._db.execute(
            select(FoodItem).where(FoodItem.is_available.is_(True)).limit(limit)
        )
        return list(result.scalars().all())

    async def search_by_dietary_tag(self, tag: str) -> list[FoodItem]:
        """Find food items containing a dietary tag (e.g. vegetarian)."""
        result = await self._db.execute(
            select(FoodItem).where(
                FoodItem.is_available.is_(True),
                FoodItem.dietary_tags.contains([tag]),
            )
        )
        return list(result.scalars().all())
