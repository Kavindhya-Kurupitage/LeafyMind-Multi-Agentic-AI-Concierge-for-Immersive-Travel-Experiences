"""Trip pack PDF — Unicode in LLM copy must not break generation."""

from services.trip_pdf_service import TripPdfService, _pdf_safe_text


def test_pdf_safe_text_replaces_em_dash():
    assert "—" not in _pdf_safe_text("Spice level — mild and fragrant")
    assert "-" in _pdf_safe_text("Spice level — mild")


def test_generate_pdf_with_unicode_narrative():
    summary = {
        "guest_name": "Sewwandi",
        "profile": {
            "group_type": "couple",
            "travel_style": "romance",
            "duration_nights": 2,
            "dietary_restrictions": "none",
        },
        "packages": {
            "narrative": "A perfect stay — tailored for you.",
            "recommendations": [
                {
                    "package_name": "Love Nest Getaway",
                    "price_per_night_usd": 120,
                    "min_nights": 2,
                    "why_this_fits": "As a couple — you'll love the views.",
                    "inclusions": ["Breakfast", "Private cabana"],
                }
            ],
        },
        "food": {
            "narrative": "Must-try dishes — start mild.",
            "must_try": [
                {
                    "dish_name": "Hoppers",
                    "spice_level": "mild",
                    "description": "Bowl-shaped pancakes — crispy edges.",
                }
            ],
        },
        "itinerary": {
            "narrative": "Day trips — relaxed pace.",
            "itinerary": [
                {
                    "day": 1,
                    "theme": "Waterfalls",
                    "activities": [
                        {
                            "time_slot": "Morning",
                            "attraction_name": "Diyaluma Falls",
                            "description": "Scenic hike — bring water.",
                        }
                    ],
                }
            ],
        },
    }
    pdf = TripPdfService().generate_pdf(summary)
    assert isinstance(pdf, bytes)
    assert pdf[:4] == b"%PDF"
