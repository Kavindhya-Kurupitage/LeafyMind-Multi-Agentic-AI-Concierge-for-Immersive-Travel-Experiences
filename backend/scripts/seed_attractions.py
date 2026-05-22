"""Seed verified attractions near Leafy Cave, Wellawaya."""

import asyncio
from decimal import Decimal

from sqlalchemy import delete

from database import AsyncSessionLocal, init_db
from models.attraction import Attraction
from models.enums import AttractionCategory, FitnessLevel

ATTRACTIONS = [
    {
        "name": "Ella Wala Falls",
        "category": AttractionCategory.WATERFALL,
        "description": (
            "A small but beautiful waterfall hidden deep within the "
            "jungle along the Ella–Wellawaya Road. Famous for its natural pool with "
            "clear, cool water — perfect for a refreshing swim. The jungle trek to "
            "reach it is part of the adventure."
        ),
        "distance_km_from_cabana": Decimal("18.0"),
        "estimated_duration_hours": Decimal("3.0"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.MODERATE,
        "suitable_for": ["solo", "couple", "family", "group"],
        "tips": (
            "Wear waterproof sandals. The jungle path gets slippery after rain. "
            "Best visited in the morning before afternoon crowds."
        ),
        "latitude": Decimal("6.8670"),
        "longitude": Decimal("81.0460"),
        "seasonal_availability": {"all_year": True},
    },
    {
        "name": "Ravana Adventure Park (Pallewala Waterfall)",
        "category": AttractionCategory.HIKING,
        "description": (
            "An adventure park offering waterfall abseiling, zip line, "
            "rappelling, rock climbing, bird watching, hiking, waterfall and village "
            "trekking, and slithering rock experiences. All activities are supervised "
            "by experienced instructors with maximum safety standards. A bathing ticket "
            "is included; adventure activities require separate tickets."
        ),
        "distance_km_from_cabana": Decimal("22.0"),
        "estimated_duration_hours": Decimal("5.0"),
        "entry_fee_usd": Decimal("3.0"),
        "fitness_level_required": FitnessLevel.HIGH,
        "suitable_for": ["solo", "couple", "group"],
        "tips": (
            "Book activity tickets in advance during peak season. Minimum age "
            "for zip line is 12 years. Bring a change of clothes — you will get wet."
        ),
        "latitude": Decimal("6.9271"),
        "longitude": Decimal("81.0490"),
        "seasonal_availability": {"all_year": True},
    },
    {
        "name": "Diyaluma Waterfall",
        "category": AttractionCategory.WATERFALL,
        "description": (
            "Sri Lanka's second tallest waterfall at 220 meters, located "
            "near Koslanda. Famous for its stunning natural pools at the top and the "
            "panoramic view of the lush landscape below. Popular for both swimming and "
            "sightseeing. A spectacular destination for nature lovers and adventure "
            "seekers alike."
        ),
        "distance_km_from_cabana": Decimal("28.0"),
        "estimated_duration_hours": Decimal("4.0"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.MODERATE,
        "suitable_for": ["solo", "couple", "family", "group"],
        "tips": (
            "The climb to the top pools takes about 45 minutes — wear good "
            "shoes. Go early to get the pools before they get crowded. The view from "
            "the top is worth every step."
        ),
        "latitude": Decimal("6.7968"),
        "longitude": Decimal("80.9897"),
        "seasonal_availability": {
            "all_year": True,
            "best_months": ["Nov", "Dec", "Jan", "Feb"],
        },
    },
    {
        "name": "Handapanagala Lake",
        "category": AttractionCategory.WILDLIFE,
        "description": (
            "A picturesque lake located 16 km from Wellawaya near "
            "Handapanagala Junction. Surrounded by rocky plains, the tank remains "
            "full of water year-round, fed by the Kirindi River. Popular with both "
            "locals and tourists for its serene beauty and wildlife sightings."
        ),
        "distance_km_from_cabana": Decimal("16.0"),
        "estimated_duration_hours": Decimal("2.0"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.LOW,
        "suitable_for": ["solo", "couple", "family", "group"],
        "tips": (
            "Visit in the evening for the best experience — golden hour "
            "reflections on the water are stunning. Elephants are sometimes spotted "
            "near the tank at dusk."
        ),
        "latitude": Decimal("6.6910"),
        "longitude": Decimal("81.1350"),
        "seasonal_availability": {"all_year": True, "recommended_time": "evening"},
    },
    {
        "name": "Alikota Ara Reservoir",
        "category": AttractionCategory.CULTURAL,
        "description": (
            "A large reservoir in Pahala-Uva, Wellawaya with a dam "
            "stretching 750 meters long and 28 meters high, built across the Alikota "
            "Ara stream. Part of the Uma Oya Downstream Development Project (2014). "
            "Surrounded by natural beauty — a serene and scenic spot for photography "
            "and peaceful walks."
        ),
        "distance_km_from_cabana": Decimal("10.0"),
        "estimated_duration_hours": Decimal("1.5"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.LOW,
        "suitable_for": ["solo", "couple", "family", "group"],
        "tips": (
            "Great for sunrise photography. The dam walkway offers sweeping "
            "views of the reservoir and surrounding hills. Very close to the cabana — "
            "ideal for an easy morning outing."
        ),
        "latitude": Decimal("6.7450"),
        "longitude": Decimal("81.0800"),
        "seasonal_availability": {"all_year": True},
    },
    {
        "name": "Kalu Wala Falls",
        "category": AttractionCategory.WATERFALL,
        "description": (
            "A beautiful jungle waterfall with a natural pool, hidden "
            "along the Ella–Wellawaya Road. Similar to Ella Wala Falls but quieter "
            "and less visited — ideal for guests who want a more private nature "
            "experience. The cool, clear water makes it perfect for a refreshing "
            "jungle swim."
        ),
        "distance_km_from_cabana": Decimal("20.0"),
        "estimated_duration_hours": Decimal("2.5"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.MODERATE,
        "suitable_for": ["solo", "couple", "family", "group"],
        "tips": (
            "Often overlooked by tourists — you may have it to yourself on "
            "weekdays. Combined well with an Ella Wala Falls visit on the same day."
        ),
        "latitude": Decimal("6.8800"),
        "longitude": Decimal("81.0500"),
        "seasonal_availability": {"all_year": True},
    },
    {
        "name": "Ella Rock & Ella Gap Viewpoint",
        "category": AttractionCategory.HIKING,
        "description": (
            "One of Sri Lanka's most iconic hikes offering panoramic "
            "views of the Ella Gap and surrounding tea-covered hills. The trail passes "
            "through tea plantations and jungle. The summit rewards hikers with a "
            "breathtaking 360-degree view. A must-do for any guest with moderate "
            "fitness staying in the Ella–Wellawaya area."
        ),
        "distance_km_from_cabana": Decimal("35.0"),
        "estimated_duration_hours": Decimal("5.0"),
        "entry_fee_usd": Decimal("0.0"),
        "fitness_level_required": FitnessLevel.HIGH,
        "suitable_for": ["solo", "couple", "group"],
        "tips": (
            "Start by 6:30 AM to reach the summit before clouds roll in "
            "(usually by 10 AM). Wear proper hiking shoes. Bring water and a light "
            "snack. No guide needed but local guides available at the trailhead."
        ),
        "latitude": Decimal("6.8667"),
        "longitude": Decimal("81.0460"),
        "seasonal_availability": {
            "all_year": True,
            "avoid": ["May", "Jun", "heavy_rain_days"],
        },
    },
]


async def seed() -> None:
    """Replace placeholder attractions with seven verified Wellawaya-area places."""
    await init_db()
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Attraction))
        await db.flush()
        for data in ATTRACTIONS:
            db.add(Attraction(**data))
        await db.commit()
    print(
        f"Seeded {len(ATTRACTIONS)} Leafy Cave attractions "
        "(replaced all previous rows)."
    )


if __name__ == "__main__":
    asyncio.run(seed())
