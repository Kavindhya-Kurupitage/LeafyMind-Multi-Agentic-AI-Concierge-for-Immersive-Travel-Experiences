"""Single source of truth for attraction and location data queries."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.attraction import Attraction
from models.enums import AttractionCategory, FitnessLevel
from rules.business_rules import AttractionRules, ItineraryRules
from services.distance_calculator import distance_calculator
from services.opentripmap_service import opentripmap_service

# Guest interest keywords → OpenTripMap kinds
OPENTRIPMAP_KINDS_MAP: dict[str, list[str]] = {
    "wildlife": ["parks", "natural"],
    "waterfall": ["natural"],
    "waterfalls": ["natural"],
    "temple": ["cultural", "religion"],
    "temples": ["cultural", "religion"],
    "hiking": ["sport", "natural"],
    "hike": ["sport", "natural"],
    "beach": ["beaches", "natural"],
    "beaches": ["beaches", "natural"],
    "cultural": ["cultural", "historic"],
    "culture": ["cultural", "historic"],
    "nature": ["natural", "parks"],
    "adventure": ["sport", "natural"],
    "relaxation": ["natural", "cultural"],
}


class AttractionDataLayer:
    """Encapsulates all database access for attractions — no other module should query directly."""

    INTEREST_CATEGORY_MAP: dict[str, list[AttractionCategory]] = {
        "culture": [AttractionCategory.CULTURAL, AttractionCategory.TEMPLE],
        "cultural": [AttractionCategory.CULTURAL, AttractionCategory.TEMPLE],
        "nature": [AttractionCategory.WILDLIFE, AttractionCategory.WATERFALL, AttractionCategory.HIKING],
        "wildlife": [AttractionCategory.WILDLIFE],
        "adventure": [AttractionCategory.HIKING, AttractionCategory.WILDLIFE],
        "hiking": [AttractionCategory.HIKING],
        "waterfall": [AttractionCategory.WATERFALL],
        "beach": [AttractionCategory.BEACH],
        "food": [AttractionCategory.FOOD_EXPERIENCE],
        "relaxation": [AttractionCategory.WATERFALL, AttractionCategory.CULTURAL],
    }

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._rules = AttractionRules()

    async def list_all(self, limit: int = 50) -> list[Attraction]:
        """Return active attractions ordered by distance from cabana."""
        result = await self._db.execute(
            select(Attraction)
            .where(Attraction.is_active.is_(True))
            .order_by(Attraction.distance_km_from_cabana.asc().nulls_last())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, attraction_id: str | uuid.UUID) -> Attraction | None:
        """Fetch a single attraction by primary key."""
        aid = uuid.UUID(str(attraction_id)) if isinstance(attraction_id, str) else attraction_id
        result = await self._db.execute(select(Attraction).where(Attraction.id == aid))
        return result.scalar_one_or_none()

    async def search_by_category(self, category: AttractionCategory | str) -> list[Attraction]:
        """Find attractions matching a category."""
        if isinstance(category, str):
            category = AttractionCategory(category)
        result = await self._db.execute(
            select(Attraction).where(
                Attraction.category == category,
                Attraction.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def get_filtered_attractions(
        self,
        profile: dict[str, Any],
        include_discovered: bool = True,
    ) -> dict[str, Any]:
        """
        Return curated DB attractions and optional OpenTripMap discoveries.

        {
          "curated": [Attraction, ...],
          "discovered": [dict, ...],
          "discoveries_loaded": bool,
        }
        """
        curated = await self._get_curated_attractions(profile)
        discovered: list[dict[str, Any]] = []
        discoveries_loaded = False

        if include_discovered:
            discovered, discoveries_loaded = await self.fetch_discoveries_for_gaps(
                profile, curated
            )

        return {
            "curated": curated,
            "discovered": discovered,
            "discoveries_loaded": discoveries_loaded,
        }

    async def fetch_discoveries_for_gaps(
        self,
        profile: dict[str, Any],
        curated: list[Attraction],
        *,
        min_curated: int = 4,
    ) -> tuple[list[dict[str, Any]], bool]:
        """
        Query OpenTripMap only after curated rules filtering, when verified
        attractions do not fully cover the guest's interests.
        """
        if not settings.opentripmap_api_key.strip():
            return [], False

        interests = [str(i).lower() for i in (profile.get("interests") or [])]
        if len(curated) >= min_curated and not self._interests_uncovered(curated, interests):
            return [], False

        kinds = self._kinds_for_interests(interests)
        radius = min(80, int(settings.max_search_radius_km))
        raw_places = await opentripmap_service.search_nearby_places(
            kinds=kinds,
            radius_km=radius,
            limit=8,
        )
        discovered = distance_calculator.enrich_with_distance(
            raw_places,
            settings.cabana_lat,
            settings.cabana_lon,
        )
        curated_names = {a.name.lower().strip() for a in curated}
        discovered = [
            p
            for p in discovered
            if p.get("name", "").lower().strip() not in curated_names
        ]
        fitness = (profile.get("fitness_level") or "moderate").lower()
        if fitness == "low":
            discovered = [
                p for p in discovered if (p.get("distance_km") or 999) <= 30
            ]
        return discovered, True

    def apply_suitability_filters(
        self, attractions: list[Attraction], profile: dict[str, Any]
    ) -> list[Attraction]:
        """Filter by group type and guest interests."""
        group_type = (profile.get("group_type") or "couple").lower()
        interests = [str(i).lower() for i in (profile.get("interests") or [])]

        result: list[Attraction] = []
        for att in attractions:
            suitable = [str(s).lower() for s in (att.suitable_for or [])]
            if suitable and group_type not in suitable:
                if group_type == "family" and "couple" in suitable:
                    pass
                elif group_type not in suitable:
                    continue

            if interests:
                categories = self._categories_for_interests(interests)
                if categories and att.category not in categories:
                    continue

            result.append(att)
        return result

    @staticmethod
    def _interests_uncovered(
        curated: list[Attraction], interests: list[str]
    ) -> bool:
        """True when guest interests are not represented in curated categories."""
        if not interests:
            return False
        curated_cats = {a.category.value for a in curated}
        interest_keywords = {
            "wildlife": "wildlife",
            "waterfall": "waterfall",
            "hiking": "hiking",
            "hike": "hiking",
            "adventure": "hiking",
            "cultural": "cultural",
            "culture": "cultural",
            "nature": "wildlife",
        }
        for interest in interests:
            cat = interest_keywords.get(interest)
            if cat and cat not in curated_cats:
                return True
        return False

    async def _get_curated_attractions(self, profile: dict[str, Any]) -> list[Attraction]:
        """Filter attractions by guest profile; sort by distance; return max 10."""
        all_attractions = await self.list_all(limit=50)
        fitness = (profile.get("fitness_level") or "moderate").lower()
        group_type = (profile.get("group_type") or "couple").lower()
        interests = [str(i).lower() for i in (profile.get("interests") or [])]
        arrival_date = profile.get("arrival_date")
        duration_nights = int(profile.get("duration_nights") or 3)
        travel_style = (profile.get("travel_style") or "").lower()

        filtered = self._rules.filter_by_fitness(all_attractions, fitness)
        filtered = self._rules.filter_by_duration(filtered, duration_nights)

        result: list[Attraction] = []
        for att in filtered:
            suitable = [str(s).lower() for s in (att.suitable_for or [])]
            if suitable and group_type not in suitable:
                if group_type == "family" and "couple" in suitable:
                    pass
                elif group_type not in suitable:
                    continue

            if interests:
                categories = self._categories_for_interests(interests)
                if categories and att.category not in categories:
                    continue

            result.append(att)

        if travel_style == "workation":
            workation = self._rules.get_workation_attractions(result)
            result = workation["weekday_recommended"] or result

        result = self._rules.filter_seasonal(result, arrival_date)
        result.sort(key=lambda a: float(a.distance_km_from_cabana or 999))
        return result[:10]

    @staticmethod
    def _kinds_for_interests(interests: list[Any]) -> list[str]:
        """Map guest interests to OpenTripMap kind strings."""
        kinds: list[str] = []
        for interest in interests:
            key = str(interest).lower()
            for map_key, map_kinds in OPENTRIPMAP_KINDS_MAP.items():
                if map_key in key:
                    kinds.extend(map_kinds)
        return list(dict.fromkeys(kinds)) or ["natural", "cultural"]

    async def optimize_day_routes(
        self,
        attraction_ids: list[str | uuid.UUID],
        duration_nights: int,
        fitness_level: str | None = None,
    ) -> list[list[Attraction]]:
        """Group attractions into day-sized chunks for the stay duration."""
        attractions: list[Attraction] = []
        for aid in attraction_ids:
            att = await self.get_by_id(aid)
            if att:
                attractions.append(att)

        if not attractions:
            return []

        num_days = max(1, min(int(duration_nights or 1), 14))
        max_per_day = self._rules.max_activities_per_day(fitness_level or "moderate")

        fitness_order = {"high": 0, "moderate": 1, "low": 2}
        sorted_atts = sorted(
            attractions,
            key=lambda a: (
                fitness_order.get(a.fitness_level_required.value, 1),
                float(a.distance_km_from_cabana or 999),
            ),
        )

        days: list[list[Attraction]] = [[] for _ in range(num_days)]
        day_idx = 0
        for att in sorted_atts:
            if len(days[day_idx]) >= max_per_day:
                day_idx = (day_idx + 1) % num_days
            days[day_idx].append(att)
            if len(days[day_idx]) >= max_per_day:
                day_idx = (day_idx + 1) % num_days

        return [day for day in days if day]

    def _categories_for_interests(
        self, interests: list[str]
    ) -> list[AttractionCategory]:
        """Map guest interest keywords to attraction categories."""
        categories: list[AttractionCategory] = []
        for interest in interests:
            for key, cats in self.INTEREST_CATEGORY_MAP.items():
                if key in interest:
                    categories.extend(cats)
        return list(dict.fromkeys(categories))
