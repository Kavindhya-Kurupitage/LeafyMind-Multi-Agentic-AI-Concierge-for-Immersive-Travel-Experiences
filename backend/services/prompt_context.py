"""Static prompt context snippets for Leafy Cave concierge agents."""

LEAFY_CAVE_CONTEXT = """
Leafy Cave is a luxury eco-cabana retreat in Sri Lanka, offering warm hospitality,
curated stays, and culturally respectful guidance for international guests.
Respect local customs: modest dress at temples, remove shoes where appropriate,
and greet with a smile. Currency: USD for packages; LKR for local purchases.
Peak seasons: December–March, July–August.
"""

FOOD_CULTURE_SNIPPET = """
Sri Lankan cuisine features rice and curry, hoppers (appa), kottu roti, and
fresh seafood. Mention spice levels gently and always note vegetarian options
(coconut sambol, dal, mallung).
"""

TEMPLE_ETIQUETTE = """
When visiting temples: cover shoulders and knees, remove footwear, and avoid
turning your back to Buddha statues for photographs.
"""


def get_property_context() -> str:
    """Return core property context for system prompts."""
    return LEAFY_CAVE_CONTEXT.strip()


def get_food_context() -> str:
    """Return food culture context for the Food Guide agent."""
    return FOOD_CULTURE_SNIPPET.strip()


def get_cultural_guidelines() -> str:
    """Return cultural etiquette snippets for itinerary and attraction agents."""
    return TEMPLE_ETIQUETTE.strip()
