"""Tests for AttractionRules seasonal warnings."""

from decimal import Decimal
from types import SimpleNamespace

from rules.business_rules import AttractionRules


def test_seasonal_warning_for_ella_rock_in_may():
    rules = AttractionRules()
    att = SimpleNamespace(
        name="Ella Rock & Ella Gap Viewpoint",
        seasonal_availability={"all_year": True, "avoid": ["May", "Jun"]},
    )
    warnings = rules.flag_seasonal_warnings([att], "May")
    assert len(warnings) == 1
    assert "Ella Rock" in warnings[0]


def test_filter_seasonal_excludes_ella_rock_in_june():
    rules = AttractionRules()
    att = SimpleNamespace(
        name="Ella Rock & Ella Gap Viewpoint",
        seasonal_availability={"all_year": True, "avoid": ["May", "Jun"]},
        distance_km_from_cabana=Decimal("35.0"),
    )
    lake = SimpleNamespace(
        name="Handapanagala Lake",
        seasonal_availability={"all_year": True},
        distance_km_from_cabana=Decimal("16.0"),
    )
    filtered = rules.filter_seasonal(
        [att, lake], "2026-06-15"
    )
    names = {a.name for a in filtered}
    assert "Ella Rock & Ella Gap Viewpoint" not in names
    assert "Handapanagala Lake" in names
