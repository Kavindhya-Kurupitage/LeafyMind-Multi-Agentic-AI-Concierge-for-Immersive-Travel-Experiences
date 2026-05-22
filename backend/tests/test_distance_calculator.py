"""Tests for Haversine distance near Wellawaya."""

from services.distance_calculator import distance_calculator

# Leafy Cave / Wellawaya cabana
CABANA_LAT = 6.7311
CABANA_LON = 81.1003

# Approximate Ravana Falls area (seed data lists ~12 km from cabana)
RAVANA_LAT = 6.8644
RAVANA_LON = 81.0556


def test_haversine_ravana_falls_approx_12km():
    dist = distance_calculator.haversine_distance(
        CABANA_LAT, CABANA_LON, RAVANA_LAT, RAVANA_LON
    )
    assert 8 <= dist <= 18, f"Expected ~12km, got {dist}km"


def test_travel_time_formatting():
    short = distance_calculator.estimate_travel_time(10)
    assert "min drive" in short["formatted"]

    long = distance_calculator.estimate_travel_time(50)
    assert "hr" in long["formatted"]


def test_enrich_with_distance_sorts_nearest_first():
    places = [
        {"name": "Far", "lat": 7.2, "lon": 81.5},
        {"name": "Near", "lat": 6.75, "lon": 81.08},
    ]
    enriched = distance_calculator.enrich_with_distance(places, CABANA_LAT, CABANA_LON)
    assert enriched[0]["name"] == "Near"
    assert enriched[0]["distance_km"] is not None
    assert enriched[0]["travel_time"]["formatted"]
