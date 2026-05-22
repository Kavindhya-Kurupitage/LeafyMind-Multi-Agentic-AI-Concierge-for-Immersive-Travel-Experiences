"""Food Guide agent — personalised Sri Lankan cuisine recommendations."""

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from models.food_item import FoodItem
from models.guest_profile import GuestProfile
from rules.business_rules import FoodRules
from services.food_data_layer import FoodDataLayer
from services.prompt_context import get_food_context, get_property_context
from services.food_image_service import food_image_service

FOOD_SYSTEM_PROMPT = """You are a Sri Lankan cuisine expert helping international tourists understand local food.
Use plain, friendly English. Always mention spice levels clearly.
For vegetarians/vegans, be specific about which dishes work.
Make food sound delicious and approachable — Sri Lankan cuisine is one of the world's most flavorful.
Never guess about allergens — only state what is in the knowledge base provided.
After your narrative, you MUST end with a JSON block on its own lines:
```json
{"must_try": ["dish1", "dish2", "dish3"], "safe_starter": "dish name", "dishes_to_avoid": ["dish"]}
```"""


class FoodGuideAgent(BaseAgent):
    """Suggests dishes and dining guidance with cultural sensitivity."""

    agent_name = "FoodGuideAgent"

    def __init__(
        self,
        llm_service: Any,
        knowledge_base: Any,
        db: AsyncSession,
    ) -> None:
        super().__init__(llm_service, knowledge_base)
        self._food_layer = FoodDataLayer(db)

    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:
        """Generate a personalised food guide for the guest profile."""
        profile_data = payload.get("guest_profile", {})
        agent_preferences = payload.get("agent_preferences") or {}
        profile = (
            profile_data
            if isinstance(profile_data, GuestProfile)
            else GuestProfile.from_dict(profile_data)
        )

        all_items = await self._food_layer.list_available(limit=50)
        filtered = FoodRules.filter_by_dietary(all_items, profile.dietary_restrictions)
        avoid = FoodRules.flag_allergens(filtered, profile.dietary_restrictions)

        context = self._build_food_context(filtered)
        prefs_block = json.dumps(agent_preferences, default=str) if agent_preferences else "none"
        meal_count = agent_preferences.get("meal_plan_count") or (profile.duration_nights or 3) * 3
        prompt = (
            f"Guest profile (from Profile Builder):\n"
            f"- Dietary: {profile.dietary_restrictions}\n"
            f"- Origin: {profile.origin_country}\n"
            f"- Stay: {profile.duration_nights} nights\n\n"
            f"Food preferences gathered in conversation:\n{prefs_block}\n\n"
            f"Plan for approximately {meal_count} meals across the stay.\n\n"
            f"Available dishes from our knowledge base ONLY:\n{context}\n\n"
            "Write a personalised food guide. Pick 3 must-try dishes and 1 safe starter for first-timers."
        )
        system = f"{FOOD_SYSTEM_PROMPT}\n\n{get_property_context()}\n{get_food_context()}"
        raw_narrative = await self._llm.invoke(prompt, system)

        structured = self._parse_food_json(raw_narrative)
        narrative = self._strip_json_block(raw_narrative)

        must_try_names = self._coerce_dish_names(structured.get("must_try")) or self._default_must_try(filtered)
        safe_starter_name = self._coerce_dish_name(structured.get("safe_starter")) or self._default_safe_starter(filtered)
        dishes_to_avoid = structured.get("dishes_to_avoid") or avoid

        must_try = [self._build_dish_record(name, filtered) for name in must_try_names[:3]]
        safe_starter = self._build_dish_record(safe_starter_name, filtered)

        dish_names = [d["dish_name"] for d in must_try] + [safe_starter["dish_name"]]
        images_by_dish = await food_image_service.get_images_for_dishes(dish_names)

        must_try = [self._attach_image(dish, images_by_dish.get(dish["dish_name"])) for dish in must_try]
        safe_starter = self._attach_image(safe_starter, images_by_dish.get(safe_starter["dish_name"]))

        self._log_agent_call(
            self.agent_name,
            f"dietary={profile.dietary_restrictions}",
            f"must_try={[d['dish_name'] for d in must_try]}",
        )

        return {
            "must_try": must_try,
            "safe_starter": safe_starter,
            "dishes_to_avoid": dishes_to_avoid,
            "narrative": narrative.strip(),
            "agent_used": self.agent_name,
        }

    async def run(self, message: str, user_id: str | None = None) -> str:
        """Backward-compatible entry point."""
        result = await self.process({"guest_profile": {}}, {})
        return result.get("narrative", "")

    def _build_food_context(self, items: list[FoodItem]) -> str:
        """Format food items for the LLM prompt."""
        if not items:
            return "No dishes available in knowledge base."
        lines = []
        for item in items:
            allergens = ", ".join(item.allergens or []) or "none listed"
            tags = ", ".join(item.dietary_tags or [])
            lines.append(
                f"- {item.name} ({item.meal_type.value}, spice: {item.spice_level.value})\n"
                f"  {item.description_plain_english or ''}\n"
                f"  Ingredients: {', '.join(item.ingredients or [])}\n"
                f"  Dietary tags: {tags}; Allergens: {allergens}\n"
                f"  Note: {item.cultural_note or ''}"
            )
        return "\n".join(lines)

    def _parse_food_json(self, raw: str) -> dict[str, Any]:
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        text = fence.group(1) if fence else raw
        start = text.rfind("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {}

    def _strip_json_block(self, raw: str) -> str:
        return re.sub(r"```json\s*\{.*?\}\s*```", "", raw, flags=re.DOTALL).strip()

    def _default_must_try(self, items: list[FoodItem]) -> list[str]:
        mild_first = sorted(items, key=lambda i: i.spice_level.value)
        return [i.name for i in mild_first[:3]]

    def _default_safe_starter(self, items: list[FoodItem]) -> str:
        for item in items:
            if item.spice_level.value == "mild":
                return item.name
        return items[0].name if items else "Rice and Curry"

    @staticmethod
    def _coerce_dish_name(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return str(value.get("dish_name") or value.get("name") or "").strip() or None
        text = str(value).strip()
        return text or None

    @classmethod
    def _coerce_dish_names(cls, value: Any) -> list[str]:
        if not value:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, list):
            names: list[str] = []
            for item in value:
                name = cls._coerce_dish_name(item)
                if name:
                    names.append(name)
            return names
        return []

    def _find_food_item(self, dish_name: str, items: list[FoodItem]) -> FoodItem | None:
        key = dish_name.lower().strip()
        for item in items:
            if item.name.lower().strip() == key:
                return item
        for item in items:
            if key in item.name.lower() or item.name.lower() in key:
                return item
        return None

    def _build_dish_record(self, dish_name: str, items: list[FoodItem]) -> dict[str, Any]:
        """Build a structured dish payload from the knowledge base when possible."""
        item = self._find_food_item(dish_name, items)
        if item:
            return {
                "dish_name": item.name,
                "description_plain_english": item.description_plain_english or "",
                "spice_level": item.spice_level.value,
                "dietary_tags": list(item.dietary_tags or []),
                "allergen_flags": list(item.allergens or []),
                "cultural_note": item.cultural_note or "",
                "image": None,
            }
        return {
            "dish_name": dish_name,
            "description_plain_english": "",
            "spice_level": "medium",
            "dietary_tags": [],
            "allergen_flags": [],
            "cultural_note": "",
            "image": None,
        }

    @staticmethod
    def _attach_image(dish: dict[str, Any], image_data: dict[str, Any] | None) -> dict[str, Any]:
        updated = dict(dish)
        updated["image"] = image_data
        return updated

    @staticmethod
    def dish_display_names(must_try: list[Any]) -> list[str]:
        """Extract dish names from structured or legacy must_try payloads."""
        names: list[str] = []
        for entry in must_try:
            if isinstance(entry, dict):
                name = entry.get("dish_name") or entry.get("name")
                if name:
                    names.append(str(name))
            elif entry:
                names.append(str(entry))
        return names
