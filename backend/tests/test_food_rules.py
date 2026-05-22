"""Tests for FoodRules dietary exclusions."""

from types import SimpleNamespace

from rules.business_rules import FoodRules


def _food(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, allergens=[], dietary_tags=[])


def test_vegetarian_excludes_fish_and_kottu():
    items = [
        _food("Fish Ambul Thiyal"),
        _food("Kottu Roti"),
        _food("Dhal Curry (Parippu)"),
        _food("Rice and Curry"),
    ]
    filtered = FoodRules.filter_by_dietary(items, "vegetarian")
    names = {f.name for f in filtered}
    assert "Fish Ambul Thiyal" not in names
    assert "Kottu Roti" not in names
    assert "Dhal Curry (Parippu)" in names


def test_safe_starter_vegetarian():
    items = [_food("Dhal Curry (Parippu)"), _food("Rice and Curry")]
    starter = FoodRules.get_safe_starter(items, "vegetarian")
    assert starter == "Dhal Curry (Parippu)"


def test_safe_starter_default():
    items = [_food("Egg Hoppers"), _food("Rice and Curry")]
    starter = FoodRules.get_safe_starter(items, None)
    assert starter == "Egg Hoppers"
