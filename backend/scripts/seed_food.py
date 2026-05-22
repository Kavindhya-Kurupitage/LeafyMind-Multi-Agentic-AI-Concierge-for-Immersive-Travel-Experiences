"""Seed authentic Sri Lankan dishes for the Food Guide."""

import asyncio

from sqlalchemy import select

from database import AsyncSessionLocal, init_db
from models.enums import MealType, SpiceLevel
from models.food_item import FoodItem

FOOD_ITEMS = [
    {
        "name": "Rice and Curry",
        "description_plain_english": (
            "Steamed rice served with several curries — often dal, vegetables, papadam, "
            "and a choice of fish or chicken. The staple meal across Sri Lanka."
        ),
        "ingredients": [
            "basmati or local rice",
            "red lentil dal",
            "seasonal vegetables",
            "coconut milk",
            "curry leaves",
            "turmeric",
            "coconut sambol",
        ],
        "spice_level": SpiceLevel.MEDIUM,
        "dietary_tags": ["vegetarian_option", "halal_option"],
        "allergens": [],
        "cultural_note": "Eat with your right hand if joining a local family — optional for guests.",
        "meal_type": MealType.LUNCH,
    },
    {
        "name": "Hoppers (Appam)",
        "description_plain_english": (
            "Bowl-shaped pancakes with crispy edges, made from fermented rice flour and "
            "coconut milk. Served plain or with an egg cooked in the centre."
        ),
        "ingredients": ["rice flour", "coconut milk", "yeast", "salt", "optional egg"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegan", "vegetarian"],
        "allergens": ["gluten"],
        "cultural_note": "A beloved breakfast — best eaten fresh from a roadside hopper hut.",
        "meal_type": MealType.BREAKFAST,
    },
    {
        "name": "Kottu Roti",
        "description_plain_english": (
            "Shredded godamba roti stir-fried on a hot griddle with vegetables, egg, and "
            "your choice of chicken, beef, or cheese. Loud, rhythmic, and utterly satisfying."
        ),
        "ingredients": [
            "godamba roti",
            "cabbage",
            "carrot",
            "leeks",
            "egg",
            "chicken or beef optional",
            "chilli",
            "curry powder",
        ],
        "spice_level": SpiceLevel.HOT,
        "dietary_tags": ["vegetarian_option"],
        "allergens": ["gluten", "egg"],
        "cultural_note": "Ask for 'less spicy' — even mild versions have a gentle kick.",
        "meal_type": MealType.DINNER,
    },
    {
        "name": "Dhal Curry (Parippu)",
        "description_plain_english": (
            "Creamy red lentil curry tempered with mustard seeds, curry leaves, and onion — "
            "comforting, protein-rich, and essential at any rice-and-curry spread."
        ),
        "ingredients": ["red lentils", "coconut milk", "turmeric", "mustard seeds", "onion", "garlic"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegan", "vegetarian", "gluten_free"],
        "allergens": [],
        "cultural_note": "Often the first curry locals recommend to vegetarian guests.",
        "meal_type": MealType.LUNCH,
    },
    {
        "name": "Pol Sambol",
        "description_plain_english": (
            "Fiery fresh coconut relish with chilli, lime, and dried Maldive fish — "
            "a punchy condiment that awakens rice and curry."
        ),
        "ingredients": ["grated coconut", "dried chilli", "lime", "onion", "Maldive fish flakes", "salt"],
        "spice_level": SpiceLevel.HOT,
        "dietary_tags": ["vegetarian"],
        "allergens": ["fish"],
        "cultural_note": "Request a version without Maldive fish for a vegetarian take.",
        "meal_type": MealType.SNACK,
    },
    {
        "name": "Fish Ambul Thiyal",
        "description_plain_english": (
            "Sour black-fish curry from the south — tuna simmered with goraka (garcinia) "
            "for a tangy, dark, intensely flavoured dish."
        ),
        "ingredients": ["tuna", "goraka", "black pepper", "turmeric", "cinnamon", "pandan leaf"],
        "spice_level": SpiceLevel.MEDIUM,
        "dietary_tags": [],
        "allergens": ["fish"],
        "cultural_note": "A coastal classic — pairs beautifully with red rice.",
        "meal_type": MealType.DINNER,
    },
    {
        "name": "String Hoppers (Idiyappam)",
        "description_plain_english": (
            "Delicate nests of steamed rice noodles, soft and mild — typically served with "
            "coconut sambol and a thin curry for breakfast or dinner."
        ),
        "ingredients": ["rice flour", "water", "salt", "coconut sambol"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegetarian", "vegan"],
        "allergens": [],
        "cultural_note": "Popular on festive mornings — eat with your fingers, Sri Lankan style.",
        "meal_type": MealType.BREAKFAST,
    },
    {
        "name": "Wood Apple Juice",
        "description_plain_english": (
            "Tangy-sweet juice from the wood apple fruit — thick, aromatic, and refreshingly "
            "unlike anything in Western cuisines."
        ),
        "ingredients": ["wood apple pulp", "water", "sugar or jaggery", "lime optional"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegan", "vegetarian"],
        "allergens": [],
        "cultural_note": "Served cold at roadside stalls — shake well before drinking.",
        "meal_type": MealType.SNACK,
    },
    {
        "name": "Watalappan",
        "description_plain_english": (
            "Silky coconut custard pudding scented with jaggery, nutmeg, and cardamom — "
            "Sri Lanka's answer to crème caramel, with Muslim-Dutch heritage."
        ),
        "ingredients": ["coconut milk", "jaggery", "eggs", "nutmeg", "cardamom", "cashews optional"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegetarian"],
        "allergens": ["egg", "tree_nuts"],
        "cultural_note": "Traditional at Eid and festive gatherings — served chilled.",
        "meal_type": MealType.SNACK,
    },
    {
        "name": "Egg Hoppers",
        "description_plain_english": (
            "Crispy-edged hopper with a soft-set egg in the centre — dip the edges into "
            "sambol for the full breakfast experience."
        ),
        "ingredients": ["rice flour", "coconut milk", "egg", "salt", "oil"],
        "spice_level": SpiceLevel.MILD,
        "dietary_tags": ["vegetarian"],
        "allergens": ["egg", "gluten"],
        "cultural_note": "Order 'egg hopper' by name — vendors cook it to order in minutes.",
        "meal_type": MealType.BREAKFAST,
    },
]


async def seed() -> None:
    """Insert food items if they do not exist, then rebuild FAISS indexes."""
    await init_db()
    async with AsyncSessionLocal() as db:
        for data in FOOD_ITEMS:
            result = await db.execute(select(FoodItem).where(FoodItem.name == data["name"]))
            if result.scalar_one_or_none() is None:
                db.add(FoodItem(**data))
        await db.commit()
    print(f"Seeded {len(FOOD_ITEMS)} food items successfully.")

    try:
        from services.knowledge_base import knowledge_base

        await knowledge_base.build_from_db()
        print("FAISS knowledge base rebuilt from database.")
    except Exception as exc:
        print(f"Note: FAISS index build skipped ({exc}). Run build_from_db() after setting API keys.")


if __name__ == "__main__":
    asyncio.run(seed())
