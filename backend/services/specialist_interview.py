"""Conversational preference gathering for planning specialists after Profile Builder."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from agents.base_agent import BaseAgent
from models.guest_profile import GuestProfile
from services.llm_provider import llm_service
from services.prompt_context import get_property_context

logger = logging.getLogger(__name__)

OPTIONAL_PLANNING_AGENTS = frozenset(
    {"package_recommender", "food_guide", "itinerary_planner"}
)


@dataclass(frozen=True)
class SpecialistInterviewConfig:
    agent_id: str
    display_name: str
    system_prompt: str
    extraction_prompt: str
    required_keys: tuple[str, ...]
    seed_from_profile: tuple[str, ...]


def _estimated_meals(duration_nights: int | None) -> int:
    nights = max(1, int(duration_nights or 3))
    return nights * 3


def _profile_summary(profile: dict[str, Any]) -> str:
    gp = GuestProfile.from_dict(profile)
    parts = [
        f"Travel style: {gp.travel_style or 'unknown'}",
        f"Group: {gp.group_type or 'unknown'}"
        + (f" ({gp.group_size} guests)" if gp.group_size else ""),
        f"Budget: {gp.budget_tier or 'unknown'}",
        f"Dietary: {gp.dietary_restrictions}",
        f"Stay: {gp.duration_nights or '?'} nights",
        f"Interests: {', '.join(gp.interests) if gp.interests else 'not specified'}",
        f"Fitness: {gp.fitness_level or 'not specified'}",
        f"Origin: {gp.origin_country or 'international guest'}",
    ]
    if gp.special_occasions:
        parts.append(f"Occasion: {gp.special_occasions}")
    return "\n".join(f"- {p}" for p in parts)


INTERVIEW_CONFIGS: dict[str, SpecialistInterviewConfig] = {
    "food_guide": SpecialistInterviewConfig(
        agent_id="food_guide",
        display_name="Food Guide",
        system_prompt="""You are the Leafy Cave Food Guide specialist.
The guest already completed Profile Builder — you have their core travel profile below.
Do NOT re-ask for travel style, group, budget, or trip length unless they want to change something.

Your job BEFORE creating their food guide:
1. Greet them warmly and briefly reference their profile (diet, origin, stay length).
2. Propose a sensible meal plan count (about 3 meals per day × nights) and confirm or adjust.
3. Ask ONE focused food question per reply: spice tolerance, favourite cuisines, meal types
   (breakfast/lunch/dinner/street food), dining style (cabana meals vs local restaurants),
   extra allergies, or foods to avoid.
4. When you have enough detail, invite them to say "create my guide" or offer to generate now.

Never run a generic questionnaire — be conversational. 2–4 sentences per reply.""",
        extraction_prompt="""Extract food-planning preferences from this conversation.
Return ONLY valid JSON with any keys present:
spice_tolerance (mild|medium|hot|unknown),
meal_plan_count (integer),
meal_types (array of strings),
cuisine_interests (array),
dining_style (string),
extra_allergies (array),
foods_to_avoid (array),
wants_cooking_experience (boolean),
notes (string),
ready_to_generate (boolean — true only when guest confirmed or enough detail for a guide).
Do not invent values.""",
        required_keys=(
            "spice_tolerance",
            "meal_plan_count",
            "meal_types",
        ),
        seed_from_profile=("dietary_restrictions", "duration_nights", "origin_country"),
    ),
    "package_recommender": SpecialistInterviewConfig(
        agent_id="package_recommender",
        display_name="Package Planner",
        system_prompt="""You are the Leafy Cave Package Planner specialist.
The guest already completed Profile Builder — use their profile below; do not repeat basic profiling.

Before recommending cabana packages:
1. Acknowledge their trip (group, budget, duration, occasion if any).
2. Ask ONE question per reply about: must-haves in the stay, room/privacy preferences,
   celebration focus, add-ons (meals, excursions, spa), or flexibility on dates.
3. When ready, invite them to say "show packages" or similar to generate recommendations.

Be personal and concise (2–4 sentences).""",
        extraction_prompt="""Extract package-planning preferences from the conversation.
Return ONLY valid JSON with any keys:
package_priorities (array of strings),
room_preferences (string),
celebration_focus (string),
desired_addons (array),
date_flexibility (string),
budget_notes (string),
notes (string),
ready_to_generate (boolean).
Do not invent values.""",
        required_keys=("package_priorities", "room_preferences"),
        seed_from_profile=(
            "travel_style",
            "group_type",
            "budget_tier",
            "duration_nights",
            "special_occasions",
        ),
    ),
    "itinerary_planner": SpecialistInterviewConfig(
        agent_id="itinerary_planner",
        display_name="Itinerary Planner",
        system_prompt="""You are the Leafy Cave Itinerary Planner specialist.
The guest's Profile Builder data is below — do not re-collect basics unless they want changes.

Before building a day-by-day plan:
1. Reference their stay length, interests, and fitness from the profile.
2. Ask ONE question per reply: daily pace (relaxed vs packed), must-see themes
   (temples, wildlife, waterfalls, beaches), transport comfort, early starts OK?,
   or activities to skip.
3. When ready, invite them to say "plan my itinerary" to generate the schedule.

Use plain English. 2–4 sentences per reply.""",
        extraction_prompt="""Extract itinerary-planning preferences from the conversation.
Return ONLY valid JSON with any keys:
daily_pace (relaxed|balanced|packed),
must_see_themes (array),
transport_preference (string),
early_starts_ok (boolean),
activities_to_avoid (array),
max_drive_minutes_per_day (integer or null),
notes (string),
ready_to_generate (boolean).
Do not invent values.""",
        required_keys=("daily_pace", "must_see_themes"),
        seed_from_profile=(
            "duration_nights",
            "interests",
            "fitness_level",
            "travel_style",
        ),
    ),
}


class SpecialistInterviewService(BaseAgent):
    """Runs discovery conversation turns for planning agents."""

    agent_name = "SpecialistInterviewService"

    def __init__(self) -> None:
        super().__init__(llm_service, None)  # type: ignore[arg-type]

    async def process(
        self,
        payload: dict[str, Any],
        session_context: dict[str, Any],
    ) -> dict[str, Any]:
        """Not used — use process_turn instead."""
        return await self.process_turn(
            payload["agent_id"],
            payload["guest_profile"],
            payload.get("agent_preferences", {}),
            payload.get("conversation_history", []),
            payload.get("user_message", ""),
        )

    @staticmethod
    def seed_preferences(agent_id: str, guest_profile: dict[str, Any]) -> dict[str, Any]:
        """Pre-fill agent preferences from the shared guest profile."""
        config = INTERVIEW_CONFIGS.get(agent_id)
        if not config:
            return {}
        prefs: dict[str, Any] = {"_from_profile_builder": True}
        gp = GuestProfile.from_dict(guest_profile)
        dump = gp.model_dump()
        for key in config.seed_from_profile:
            val = dump.get(key)
            if val is not None and val != "" and val != []:
                prefs[key] = val
        if agent_id == "food_guide":
            nights = gp.duration_nights or 3
            prefs["meal_plan_count"] = _estimated_meals(nights)
            prefs["suggested_meal_plan"] = (
                f"About {_estimated_meals(nights)} meals across {nights} nights "
                "(breakfast, lunch & dinner each day)"
            )
        return prefs

    @staticmethod
    def build_opening_message(agent_id: str, guest_profile: dict[str, Any]) -> str:
        """First assistant message when a planning agent thread is created."""
        config = INTERVIEW_CONFIGS.get(agent_id)
        if not config:
            return "How can I help you plan your Leafy Cave experience?"
        summary = _profile_summary(guest_profile)
        gp = GuestProfile.from_dict(guest_profile)
        if agent_id == "food_guide":
            nights = gp.duration_nights or 3
            meals = _estimated_meals(nights)
            return (
                f"Ayubowan! I've loaded your travel profile from Profile Builder:\n{summary}\n\n"
                f"For your {nights}-night stay, I'd usually plan around **{meals} meals** "
                "(breakfast, lunch, and dinner each day) — does that sound right, or would you prefer fewer?\n\n"
                "Shall we start with your **spice tolerance** and any **meal preferences** "
                "(e.g. vegetarian dishes, street food, cabana dining only)?"
            )
        if agent_id == "package_recommender":
            return (
                f"Ayubowan! Here's what I already know from your profile:\n{summary}\n\n"
                "I'll match Leafy Cave cabana packages to this — first, what matters most to you "
                "in a stay: privacy, views, included meals, or celebration touches?\n\n"
                "Tell me any **must-haves** or **room preferences**, and I'll shortlist the best packages."
            )
        if agent_id == "itinerary_planner":
            return (
                f"Ayubowan! Your Profile Builder details are ready:\n{summary}\n\n"
                "Before I map your day-by-day adventures near Wellawaya — would you prefer a "
                "**relaxed** pace with one main outing per day, or a **packed** schedule with more sights?\n\n"
                "Any **must-see themes** (temples, wildlife, waterfalls, beaches) I should prioritise?"
            )
        return f"Hello! I have your profile:\n{summary}\n\nWhat would you like to focus on?"

    async def process_turn(
        self,
        agent_id: str,
        guest_profile: dict[str, Any],
        agent_preferences: dict[str, Any],
        conversation_history: list[dict[str, Any]],
        user_message: str,
    ) -> dict[str, Any]:
        """One discovery turn; may signal ready_to_generate."""
        config = INTERVIEW_CONFIGS.get(agent_id)
        if not config:
            return {
                "agent_response": "I'm ready when you are.",
                "agent_preferences": agent_preferences,
                "ready_to_generate": True,
            }

        prefs = dict(agent_preferences)
        summary = _profile_summary(guest_profile)
        system = (
            f"{config.system_prompt}\n\n{get_property_context()}\n\n"
            f"GUEST PROFILE (from Profile Builder):\n{summary}\n\n"
            f"Preferences collected so far for this agent:\n{json.dumps(prefs, default=str)}"
        )
        messages = self._build_messages(system, conversation_history, user_message)
        agent_response = await self._llm.invoke_messages_direct(messages)

        updated_history = conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": agent_response},
        ]
        extracted = await self._extract_preferences(config, updated_history)
        prefs.update({k: v for k, v in extracted.items() if not str(k).startswith("_")})
        ready = self._is_ready(config, prefs, extracted, user_message)

        return {
            "agent_response": agent_response,
            "agent_preferences": prefs,
            "ready_to_generate": ready,
        }

    async def _extract_preferences(
        self,
        config: SpecialistInterviewConfig,
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        transcript = "\n".join(
            f"{t.get('role', 'user').upper()}: {t.get('content', '')}"
            for t in history[-16:]
        )
        raw = await self._llm.invoke(transcript, config.extraction_prompt)
        return self._parse_json(raw)

    @staticmethod
    def _is_ready(
        config: SpecialistInterviewConfig,
        prefs: dict[str, Any],
        extracted: dict[str, Any],
        user_message: str,
    ) -> bool:
        if extracted.get("ready_to_generate"):
            return True
        lower = user_message.lower()
        triggers = (
            "create my guide",
            "show packages",
            "plan my itinerary",
            "generate",
            "ready",
            "go ahead",
            "let's do it",
            "sounds good",
            "yes please",
        )
        if any(t in lower for t in triggers):
            return True
        return all(prefs.get(k) for k in config.required_keys)

    def _parse_json(self, raw: str) -> dict[str, Any]:
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        else:
            start, end = text.find("{"), text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Specialist interview JSON parse failed: %s", raw[:200])
            return {}
