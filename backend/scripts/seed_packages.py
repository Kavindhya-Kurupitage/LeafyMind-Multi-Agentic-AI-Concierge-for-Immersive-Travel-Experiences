"""Seed Leafy Cave stay packages into the database."""

import asyncio
from decimal import Decimal

from sqlalchemy import delete, select

from database import AsyncSessionLocal, init_db
from models.enums import PackageTier
from models.package import Package

# Indicative USD per night — adjust with owner pricing when confirmed.
PACKAGES = [
    {
        "name": "Love Nest Getaway",
        "tier": PackageTier.LUXURY,
        "price_per_night_usd": Decimal("160.00"),
        "description": (
            "A romantic one-night escape designed exclusively for couples "
            "at Leafy Cave. Arrive to welcome drinks and a fruit basket, spend your "
            "evening at a personalized candlelit dinner under the stars, then gather "
            "around a bonfire with our swing experience and BBQ setup. Wake up to "
            "breakfast served in bed."
        ),
        "inclusions": [
            "Welcome drinks and fruit basket on arrival",
            "Personalized dinner under the stars",
            "Candlelit dinner setup",
            "Bonfire and swing experience",
            "Optional BBQ setup",
            "Evening beverages and snacks",
            "Breakfast in bed",
            "Drone photography shoot (complimentary)",
            "Optional adventure tours: hiking or nature walks",
        ],
        "exclusions": [
            "Adventure tour fees (optional add-on)",
            "Customized gifts (available on request)",
            "Flower decorations (available on request)",
            "Romantic picnic setup (available on request)",
        ],
        "travel_styles": ["honeymoon", "romantic", "relaxation"],
        "group_types": ["couple"],
        "min_nights": 1,
        "max_guests": 2,
        "seasonal_note": None,
        "package_meta": {
            "for_whom": "couples",
            "duration": "1 night",
            "customizations": [
                "Customized gift arrangements",
                "Flower decorations",
                "Personalized food menus",
                "Romantic picnic setup",
            ],
            "special_highlight": (
                "Drone shoots and bonfire swing experience included free"
            ),
        },
    },
    {
        "name": "Together Time Package",
        "tier": PackageTier.MID_RANGE,
        "price_per_night_usd": Decimal("92.00"),
        "description": (
            "Designed for families and groups seeking quality bonding "
            "moments at Leafy Cave. Full-board meals with customizable menus, a cozy "
            "bonfire with swing experience, optional BBQ, movie night under the stars, "
            "outdoor games, and a guided nature walk suitable for all ages."
        ),
        "inclusions": [
            "Welcome drinks and snacks on arrival",
            "Full-board meals: breakfast, lunch, dinner (customizable menu)",
            "Bonfire and swing experience",
            "Optional BBQ setup",
            "Movie night under the stars with BBQ option",
            "Outdoor games and swing access",
            "Evening beverages and snacks",
            "Drone photography shoot (complimentary)",
            "Sound system and music setup (complimentary)",
            "Optional guided nature walk",
        ],
        "exclusions": [
            "Guided nature walk fees (optional add-on)",
            "Family gift packs (available on request)",
            "Additional customized snacks (available on request)",
        ],
        "travel_styles": ["family", "cultural", "relaxation"],
        "group_types": ["family", "group"],
        "min_nights": 1,
        "max_guests": 15,
        "seasonal_note": None,
        "package_meta": {
            "for_whom": "families and friend groups",
            "duration": "1 night",
            "customizations": [
                "Customized snack packs",
                "Outdoor game selection",
                "Personalized food menus",
                "Guided nature walks",
                "Family gift packs",
            ],
            "special_highlight": (
                "Drone shoots and sound system with music included free"
            ),
        },
    },
    {
        "name": "Thrill & Chill Package",
        "tier": PackageTier.MID_RANGE,
        "price_per_night_usd": Decimal("98.00"),
        "description": (
            "A two-night escape combining adventure and relaxation at "
            "Leafy Cave. Full-board customizable meals, daily hiking, bird watching "
            "and guided tours, optional movie nights with BBQ, bonfire swing "
            "experience, and plenty of outdoor games and relaxation areas."
        ),
        "inclusions": [
            "Welcome drinks and snacks on arrival",
            "Full-board meals: breakfast, lunch, dinner (customizable menu)",
            "Daily adventure activities: hiking, bird watching, guided tours",
            "Optional movie nights with BBQ",
            "Bonfire and swing experience",
            "Optional BBQ setup",
            "Outdoor relaxation areas and games",
            "Evening beverages and snacks",
            "Drone photography shoot (complimentary)",
            "Sound system and music setup (complimentary)",
        ],
        "exclusions": [
            "Guided tour fees for external attractions",
            "Additional customized snacks (available on request)",
        ],
        "travel_styles": ["adventure", "eco", "relaxation"],
        "group_types": ["couple", "family", "group"],
        "min_nights": 2,
        "max_guests": 20,
        "seasonal_note": None,
        "package_meta": {
            "for_whom": "families, friend groups, office teams, couples",
            "duration": "2 nights",
            "customizations": [
                "Customized snack packs",
                "Outdoor game selection",
                "Personalized food menus",
                "Guided nature walks",
            ],
            "special_highlight": (
                "Drone shoots and sound system with music included free"
            ),
        },
    },
    {
        "name": "Celebration Bliss Package",
        "tier": PackageTier.MID_RANGE,
        "price_per_night_usd": Decimal("108.00"),
        "description": (
            "Designed to make your special occasions truly memorable at "
            "Leafy Cave — whether it's a birthday party, bridal shower, engagement "
            "celebration, or a get-together. Customizable event planning, full-board "
            "meals, bonfire with swing and BBQ, party games, special cakes, and sweet "
            "packs."
        ),
        "inclusions": [
            "Customizable event planning and coordination",
            "Full-board meals: lunch and dinner (customizable menu)",
            "Bonfire and swing experience",
            "BBQ setup",
            "Party games around the bonfire",
            "Evening beverages and snacks",
            "Special celebration cake",
            "Sweet packs for guests",
            "Swing and outdoor facility access",
            "Drone photography shoot (complimentary)",
            "Sound system and music setup (complimentary)",
        ],
        "exclusions": [
            "Custom decorations (available on request)",
            "Extra sweet packs (available on request)",
            "Breakfast (not included — lunch and dinner only)",
        ],
        "travel_styles": ["cultural", "relaxation", "family"],
        "group_types": ["family", "group", "couple"],
        "min_nights": 1,
        "max_guests": 30,
        "seasonal_note": "Popular December–March peak season — book early",
        "package_meta": {
            "for_whom": "special occasion groups",
            "duration": "1 night",
            "customizations": [
                "Event decorations (flowers, balloons, themes)",
                "Personalized food menus",
                "Small delicious sweet packs",
                "Themed setups for birthdays, engagements, bridal showers",
            ],
            "special_highlight": (
                "Drone shoots and sound system with music included free"
            ),
        },
    },
    {
        "name": "Remote Work Retreat",
        "tier": PackageTier.MID_RANGE,
        "price_per_night_usd": Decimal("85.00"),
        "description": (
            "Designed for professionals who work remotely and want to "
            "escape their home office without interrupting their productivity. Work "
            "from your private cabana surrounded by nature at Leafy Cave, Wellawaya. "
            "High-speed WiFi, a dedicated workspace setup, and all meals taken care "
            "of — so you focus on work during the day and unwind in nature every "
            "evening."
        ),
        "inclusions": [
            "Private cabana with dedicated work desk and ergonomic chair",
            "High-speed WiFi (stable connection guaranteed)",
            "Full-board meals: breakfast, lunch, dinner",
            "Morning tea/coffee service at your workspace",
            "Evening nature walk to decompress after work hours",
            "Bonfire and swing experience (evenings)",
            "Access to outdoor relaxation areas and hammocks",
            "Drone photography shoot (complimentary)",
            "Weekend adventure activity: hiking or bird watching (included for 2+ night stays)",
            "Quiet, distraction-free environment",
        ],
        "exclusions": [
            "Conference call setup / external monitor (bring your own devices)",
            "Adventure tour fees for external attractions",
            "Airport/station transfers (available on request)",
        ],
        "travel_styles": ["relaxation", "eco", "workation"],
        "group_types": ["solo", "couple"],
        "min_nights": 2,
        "max_guests": 4,
        "seasonal_note": "Available year-round. Best value on weekday bookings.",
        "package_meta": {
            "for_whom": "remote workers, digital nomads, work-from-home professionals",
            "duration": "2 nights minimum (flexible, up to 7 nights)",
            "customizations": [
                "Extended stay discounts (5+ nights)",
                "Healthy meal menu options",
                "Scheduled nature break itinerary around work hours",
                "Partner leisure package add-on (if travelling with a partner)",
            ],
            "special_highlight": (
                "Stable WiFi + nature environment — work productively, recharge completely"
            ),
        },
    },
]


async def seed() -> None:
    """Replace placeholder packages with the five real Leafy Cave offerings."""
    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Package))
        await db.flush()
        for data in PACKAGES:
            db.add(Package(**data))
        await db.commit()
    print(f"Seeded {len(PACKAGES)} Leafy Cave packages (replaced all previous rows).")


if __name__ == "__main__":
    asyncio.run(seed())
