"""Tests for PackageRules and AttractionRules with real Leafy Cave data."""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from rules.business_rules import (
    AttractionRules,
    PackageRules,
    filter_packages_for_profile,
)


def _pkg(
    name: str,
    tier: str,
    price: float,
    travel_styles: list[str] | None = None,
    group_types: list[str] | None = None,
    min_nights: int = 1,
    max_guests: int = 4,
    package_meta: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(),
        name=name,
        tier=SimpleNamespace(value=tier),
        price_per_night_usd=Decimal(str(price)),
        is_active=True,
        travel_styles=travel_styles or [],
        group_types=group_types or [],
        inclusions=[],
        exclusions=[],
        min_nights=min_nights,
        max_guests=max_guests,
        seasonal_note=None,
        description="",
        package_meta=package_meta or {},
    )


def _att(
    name: str,
    fitness: str,
    distance_km: float,
    suitable_for: list[str] | None = None,
    seasonal: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        fitness_level_required=SimpleNamespace(value=fitness),
        distance_km_from_cabana=Decimal(str(distance_km)),
        suitable_for=suitable_for or ["solo", "couple", "family", "group"],
        seasonal_availability=seasonal or {"all_year": True},
        category=SimpleNamespace(value="waterfall"),
    )


@pytest.fixture
def rules() -> PackageRules:
    return PackageRules()


@pytest.fixture
def catalog() -> list[SimpleNamespace]:
    return [
        _pkg(
            "Love Nest Getaway",
            "luxury",
            160,
            ["honeymoon", "romantic", "relaxation"],
            ["couple"],
            max_guests=2,
        ),
        _pkg(
            "Together Time Package",
            "mid_range",
            92,
            ["family", "cultural", "relaxation"],
            ["family", "group"],
            max_guests=15,
        ),
        _pkg(
            "Thrill & Chill Package",
            "mid_range",
            98,
            ["adventure", "eco", "relaxation"],
            ["couple", "family", "group"],
            min_nights=2,
            max_guests=20,
        ),
        _pkg(
            "Celebration Bliss Package",
            "mid_range",
            108,
            ["cultural", "relaxation", "family"],
            ["family", "group", "couple"],
            max_guests=30,
        ),
        _pkg(
            "Remote Work Retreat",
            "mid_range",
            85,
            ["relaxation", "eco", "workation"],
            ["solo", "couple"],
            min_nights=2,
            max_guests=4,
        ),
    ]


@pytest.fixture
def attractions() -> list[SimpleNamespace]:
    return [
        _att("Handapanagala Lake", "low", 16.0),
        _att("Alikota Ara Reservoir", "low", 10.0),
        _att("Ella Wala Falls", "moderate", 18.0),
        _att("Kalu Wala Falls", "moderate", 20.0),
        _att("Diyaluma Waterfall", "moderate", 28.0),
        _att("Ravana Adventure Park (Pallewala Waterfall)", "high", 22.0),
        _att(
            "Ella Rock & Ella Gap Viewpoint",
            "high",
            35.0,
            seasonal={"all_year": True, "avoid": ["May", "Jun"]},
        ),
    ]


def test_group_type_hard_filter_excludes_love_nest_for_family(
    rules: PackageRules, catalog: list
):
    filtered = rules.filter_by_group_type(catalog, "family")
    names = {p.name for p in filtered}
    assert "Love Nest Getaway" not in names
    assert "Together Time Package" in names


def test_special_occasion_boosts_love_nest_for_honeymoon(
    rules: PackageRules, catalog: list
):
    boosted = rules.filter_by_special_occasion(
        catalog, "honeymoon anniversary trip"
    )
    assert boosted[0].name == "Love Nest Getaway"


def test_filter_packages_excludes_two_night_minimum_for_one_night_stay(
    catalog: list
):
    preferences = {
        "group_type": "couple",
        "travel_style": "relaxation",
        "duration_nights": 1,
        "group_size": 2,
    }
    ranked = filter_packages_for_profile(catalog, preferences)
    names = {p.name for p in ranked}
    assert "Thrill & Chill Package" not in names
    assert "Remote Work Retreat" not in names
    assert len(ranked) >= 1


def test_romance_travel_style_scores_love_nest_for_couple(
    rules: PackageRules, catalog: list
):
    """Profile Builder uses travel_style 'romance' — must map to Love Nest styles."""
    profile = {
        "group_type": "couple",
        "travel_style": "romance",
        "duration_nights": 1,
        "group_size": 2,
    }
    love_nest = next(p for p in catalog if p.name == "Love Nest Getaway")
    together = next(p for p in catalog if p.name == "Together Time Package")
    assert rules.score_package(love_nest, profile) >= rules.score_package(
        together, profile
    )
    top = rules.get_top_packages(catalog, profile, top_n=1)
    assert top[0].name == "Love Nest Getaway"


def test_get_top_packages_empty_when_no_group_compatible_packages(
    rules: PackageRules, catalog: list
):
    """Solo guests must not fall back to couple-only Love Nest."""
    profile = {
        "group_type": "solo",
        "travel_style": "romance",
        "duration_nights": 1,
        "group_size": 1,
    }
    filtered = rules.filter_by_group_type(catalog, "solo")
    assert all(p.name != "Love Nest Getaway" for p in filtered)


def test_build_custom_package_name_for_unusual_combo(rules: PackageRules):
    name = rules.build_custom_package_name(
        {"group_type": "solo", "travel_style": "wellness", "duration_nights": 3}
    )
    assert name.startswith("Tailored Solo Wellness")
    assert "Leafy Cave" in name


def test_normalize_package_name_fuzzy(rules: PackageRules):
    assert rules.normalize_package_name("love nest getaway") == "Love Nest Getaway"
    assert rules.normalize_package_name("Together Time") == "Together Time Package"


def test_scores_differ_between_family_and_romantic_couple(
    rules: PackageRules, catalog: list
):
    family_profile = {
        "group_type": "family",
        "travel_style": "family",
        "duration_nights": 2,
    }
    romantic_profile = {
        "group_type": "couple",
        "travel_style": "romantic",
        "special_occasions": "honeymoon",
        "duration_nights": 1,
    }
    together = next(p for p in catalog if p.name == "Together Time Package")
    love_nest = next(p for p in catalog if p.name == "Love Nest Getaway")

    assert rules.score_package(together, family_profile) > rules.score_package(
        love_nest, family_profile
    )
    assert rules.score_package(love_nest, romantic_profile) > rules.score_package(
        together, romantic_profile
    )


def test_filter_packages_for_profile_ranks_family_package(catalog: list):
    preferences = {
        "group_type": "family",
        "group_size": 6,
        "travel_style": "family",
        "duration_nights": 2,
    }
    ranked = filter_packages_for_profile(catalog, preferences)
    assert ranked[0].name in ("Together Time Package", "Thrill & Chill Package")


def test_attraction_duration_filter_one_night(attractions: list):
    rules = AttractionRules()
    filtered = rules.filter_by_duration(attractions, 1)
    names = {a.name for a in filtered}
    assert "Ella Rock & Ella Gap Viewpoint" not in names
    assert "Alikota Ara Reservoir" in names


def test_attraction_fitness_filter_low(attractions: list):
    rules = AttractionRules()
    filtered = rules.filter_by_fitness(attractions, "low")
    names = {a.name for a in filtered}
    assert "Ravana Adventure Park (Pallewala Waterfall)" not in names
    assert "Handapanagala Lake" in names


def test_workation_attractions_prioritize_close_low_effort(attractions: list):
    rules = AttractionRules()
    result = rules.get_workation_attractions(attractions)
    weekday_names = {a.name for a in result["weekday_recommended"]}
    assert "Handapanagala Lake" in weekday_names
    assert "Alikota Ara Reservoir" in weekday_names
    weekend_names = {a.name for a in result["weekend_optional"]}
    assert "Ella Rock & Ella Gap Viewpoint" in weekend_names
