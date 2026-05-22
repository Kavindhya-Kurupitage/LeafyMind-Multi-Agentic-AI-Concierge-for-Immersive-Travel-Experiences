"""Rule-assisted recommendation engine for packages and experiences."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.package import Package
from rules.business_rules import filter_packages_for_profile


class RecommendationEngine:
    """Combines guest profile, business rules, and package data for suggestions."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def recommend_packages(self, guest_profile: dict[str, Any] | None) -> list[Package]:
        """Return packages ranked for the guest profile stored on the session."""
        result = await self._db.execute(select(Package).where(Package.is_active.is_(True)))
        packages = list(result.scalars().all())
        preferences = guest_profile or {}
        return filter_packages_for_profile(packages, preferences)
