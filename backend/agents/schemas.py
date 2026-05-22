"""Shared Pydantic schemas for specialist agent outputs."""

from pydantic import BaseModel, Field


class PackageRecommendation(BaseModel):
    """A single ranked package recommendation."""

    package_id: str
    name: str
    tier: str
    price_per_night_usd: float | None = None
    min_nights: int = 1
    fit_reason: str = ""


class DayActivity(BaseModel):
    """A single activity slot within a day plan."""

    time_of_day: str
    attraction_name: str
    description: str = ""
    estimated_cost_usd: float | None = None
    duration_hours: float | None = None
    source: str = "curated"  # curated | discovered
    distance_km: float | None = None
    travel_time_formatted: str | None = None
    image_url: str | None = None
    tips: str | None = None
    kinds: str | None = None


class DayPlan(BaseModel):
    """One day in a guest itinerary."""

    day_number: int
    theme: str = ""
    morning: DayActivity | None = None
    afternoon: DayActivity | None = None
    evening: str = "Relax at Leafy Cave — herbal tea and stargazing"
    estimated_day_cost_usd: float = 0.0
