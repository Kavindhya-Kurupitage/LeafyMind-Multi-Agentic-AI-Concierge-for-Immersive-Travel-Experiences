"""Scripted guided steps for Agent Hub — chips + optional free text per turn."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from agents.profile_builder import ProfileBuilderAgent
from models.guest_profile import GuestProfile

InputType = Literal[
    "single_select",
    "multi_select",
    "number_select",
    "text",
    "confirm",
    "rating",
]

GUIDED_AGENTS = frozenset(
    {
        "profile_builder",
        "package_recommender",
        "food_guide",
        "itinerary_planner",
        "feedback_collector",
    }
)


@dataclass(frozen=True)
class GuidedOption:
    id: str
    label: str
    description: str | None = None


@dataclass(frozen=True)
class GuidedStepDef:
    step_id: str
    question: str
    intro: str
    input_type: InputType
    options: tuple[GuidedOption, ...]
    profile_field: str | None = None
    preference_field: str | None = None
    allow_skip: bool = False
    allow_free_text: bool = True
    free_text_label: str = "Anything else? (optional)"
    min_selections: int = 0
    max_selections: int = 1
    is_confirm: bool = False
    is_generate_trigger: bool = False


def _opt(id_: str, label: str, desc: str | None = None) -> GuidedOption:
    return GuidedOption(id=id_, label=label, description=desc)


PROFILE_STEPS: tuple[GuidedStepDef, ...] = (
    GuidedStepDef(
        step_id="group_type",
        intro="Let's build your Leafy Cave travel profile — tap your answers below.",
        question="Who is travelling with you?",
        input_type="single_select",
        options=(
            _opt("solo", "Solo traveller"),
            _opt("couple", "Couple"),
            _opt("family", "Family"),
            _opt("group", "Group of friends"),
        ),
        profile_field="group_type",
        allow_free_text=False,
    ),
    GuidedStepDef(
        step_id="travel_style",
        intro="Wonderful — Sri Lanka has something special for every style of trip.",
        question="What kind of experience are you hoping for?",
        input_type="single_select",
        options=(
            _opt("relaxation", "Relaxation & unwind"),
            _opt("adventure", "Adventure & activity"),
            _opt("nature", "Nature & wildlife"),
            _opt("romance", "Romance & celebration"),
            _opt("wellness", "Wellness & retreat"),
            _opt("culture", "Culture & heritage"),
            _opt("luxury", "Luxury escape"),
            _opt("budget", "Simple & budget-friendly"),
        ),
        profile_field="travel_style",
    ),
    GuidedStepDef(
        step_id="budget_tier",
        intro="That helps us match the right cabana experience.",
        question="What's your budget comfort level?",
        input_type="single_select",
        options=(
            _opt("budget", "Budget-conscious"),
            _opt("mid_range", "Mid-range comfort"),
            _opt("luxury", "Luxury & indulgence"),
        ),
        profile_field="budget_tier",
    ),
    GuidedStepDef(
        step_id="dietary_restrictions",
        intro="We'll personalise food guidance and dining notes.",
        question="Any dietary needs we should know?",
        input_type="multi_select",
        options=(
            _opt("none", "No restrictions"),
            _opt("vegetarian", "Vegetarian"),
            _opt("vegan", "Vegan"),
            _opt("halal", "Halal"),
            _opt("gluten_free", "Gluten-free"),
            _opt("nut_allergy", "Nut allergy"),
            _opt("seafood_allergy", "Seafood allergy"),
        ),
        profile_field="dietary_restrictions",
        min_selections=1,
        max_selections=5,
        free_text_label="Other dietary notes (optional)",
    ),
    GuidedStepDef(
        step_id="duration_nights",
        intro="Almost there — just a few more details.",
        question="How many nights are you staying?",
        input_type="single_select",
        options=(
            _opt("2", "2 nights"),
            _opt("3", "3 nights"),
            _opt("5", "5 nights"),
            _opt("7", "7 nights"),
            _opt("10", "10 nights"),
            _opt("14", "14 nights"),
        ),
        profile_field="duration_nights",
        allow_free_text=True,
        free_text_label="Different number of nights (optional)",
    ),
    GuidedStepDef(
        step_id="interests",
        intro="We'll tailor itineraries and suggestions to what excites you.",
        question="What would you love to explore? (pick all that apply)",
        input_type="multi_select",
        options=(
            _opt("wildlife", "Wildlife & safaris"),
            _opt("temples", "Temples & culture"),
            _opt("waterfalls", "Waterfalls & hikes"),
            _opt("beaches", "Beaches & coast"),
            _opt("food", "Food & local flavours"),
            _opt("wellness", "Wellness & spa"),
        ),
        profile_field="interests",
        min_selections=1,
        max_selections=6,
    ),
    GuidedStepDef(
        step_id="fitness_level",
        intro="This helps us pace day trips near Wellawaya.",
        question="How active do you like to be on holiday?",
        input_type="single_select",
        options=(
            _opt("low", "Relaxed — easy walks"),
            _opt("moderate", "Moderate — half-day outings"),
            _opt("high", "Active — full-day adventures"),
        ),
        profile_field="fitness_level",
    ),
    GuidedStepDef(
        step_id="contact",
        intro="Optional — we can email your plan and a gentle post-stay check-in.",
        question="How should Leafy Cave reach you?",
        input_type="text",
        options=(),
        allow_skip=True,
        allow_free_text=True,
        free_text_label="Email address (optional)",
    ),
    GuidedStepDef(
        step_id="profile_confirm",
        intro="Here's what we captured for your stay.",
        question="Does this look right? Tap finish to unlock all agents.",
        input_type="confirm",
        options=(
            _opt("confirm", "Looks good — finish my profile"),
            _opt("edit", "Go back and adjust"),
        ),
        allow_free_text=False,
        is_confirm=True,
    ),
)

PACKAGE_STEPS: tuple[GuidedStepDef, ...] = (
    GuidedStepDef(
        step_id="package_priorities",
        intro="I've loaded your profile — let's find the perfect cabana package.",
        question="What matters most in your stay?",
        input_type="multi_select",
        options=(
            _opt("privacy", "Privacy & seclusion"),
            _opt("views", "Views & nature"),
            _opt("meals", "Meals included"),
            _opt("excursions", "Excursions & activities"),
            _opt("celebration", "Special celebration"),
            _opt("value", "Best value for money"),
        ),
        preference_field="package_priorities",
        min_selections=1,
        max_selections=4,
    ),
    GuidedStepDef(
        step_id="room_preferences",
        intro="Great — that narrows our recommendations.",
        question="Any room or space preferences?",
        input_type="single_select",
        options=(
            _opt("open_air", "Open-air / nature feel"),
            _opt("ensuite", "Private ensuite"),
            _opt("family_space", "Extra space for family"),
            _opt("no_preference", "No strong preference"),
        ),
        preference_field="room_preferences",
    ),
    GuidedStepDef(
        step_id="desired_addons",
        intro="Optional extras we can factor in.",
        question="Interested in any add-ons?",
        input_type="multi_select",
        options=(
            _opt("none", "None needed"),
            _opt("meals", "All meals at cabana"),
            _opt("spa", "Spa / wellness"),
            _opt("driver", "Private driver"),
            _opt("guide", "Local guide days"),
        ),
        preference_field="desired_addons",
        min_selections=1,
        max_selections=4,
    ),
    GuidedStepDef(
        step_id="package_confirm",
        intro="Ready to see packages matched to you.",
        question="Shall I find your best-matched cabana packages?",
        input_type="confirm",
        options=(_opt("generate", "Show my packages"),),
        allow_free_text=False,
        is_confirm=True,
        is_generate_trigger=True,
    ),
)

FOOD_STEPS: tuple[GuidedStepDef, ...] = (
    GuidedStepDef(
        step_id="meal_plan_confirm",
        intro="I'll plan Sri Lankan flavours around your dietary profile.",
        question="Does this meal plan sound right for your stay?",
        input_type="single_select",
        options=(
            _opt("yes", "Yes, that works"),
            _opt("fewer", "Fewer meals"),
            _opt("more", "More meals"),
        ),
        preference_field="meal_plan_confirm",
        allow_free_text=True,
        free_text_label="Preferred meal count (optional)",
    ),
    GuidedStepDef(
        step_id="spice_tolerance",
        intro="Spice is part of the adventure — we'll guide you safely.",
        question="How adventurous are you with spice?",
        input_type="single_select",
        options=(
            _opt("mild", "Mild — gentle flavours"),
            _opt("medium", "Medium — some heat"),
            _opt("hot", "Hot — bring it on"),
        ),
        preference_field="spice_tolerance",
    ),
    GuidedStepDef(
        step_id="meal_types",
        intro="We'll shape your must-try list around this.",
        question="Which meals should we plan for?",
        input_type="multi_select",
        options=(
            _opt("breakfast", "Breakfast"),
            _opt("lunch", "Lunch"),
            _opt("dinner", "Dinner"),
            _opt("street_food", "Street food experiences"),
            _opt("snacks", "Snacks & tea time"),
        ),
        preference_field="meal_types",
        min_selections=1,
        max_selections=5,
    ),
    GuidedStepDef(
        step_id="dining_style",
        intro="Almost ready to build your guide.",
        question="Where do you prefer to eat?",
        input_type="single_select",
        options=(
            _opt("cabana", "Mostly at the cabana"),
            _opt("local", "Local restaurants nearby"),
            _opt("mix", "Mix of both"),
        ),
        preference_field="dining_style",
    ),
    GuidedStepDef(
        step_id="food_confirm",
        intro="Perfect — I'll curate dishes from our kitchen knowledge base.",
        question="Create your personalised food guide?",
        input_type="confirm",
        options=(_opt("generate", "Create my food guide"),),
        allow_free_text=False,
        is_confirm=True,
        is_generate_trigger=True,
    ),
)

ITINERARY_STEPS: tuple[GuidedStepDef, ...] = (
    GuidedStepDef(
        step_id="daily_pace",
        intro="Let's map your days near Leafy Cave, Wellawaya.",
        question="What pace feels right for your trip?",
        input_type="single_select",
        options=(
            _opt("relaxed", "Relaxed — one highlight per day"),
            _opt("balanced", "Balanced — morning + afternoon"),
            _opt("packed", "Packed — see as much as possible"),
        ),
        preference_field="daily_pace",
    ),
    GuidedStepDef(
        step_id="must_see_themes",
        intro="We'll blend verified Leafy Cave picks with nearby discoveries.",
        question="Must-see themes? (pick all that apply)",
        input_type="multi_select",
        options=(
            _opt("wildlife", "Wildlife"),
            _opt("temples", "Temples & culture"),
            _opt("waterfalls", "Waterfalls"),
            _opt("hiking", "Hiking"),
            _opt("beaches", "Beaches"),
            _opt("food", "Food experiences"),
        ),
        preference_field="must_see_themes",
        min_selections=1,
        max_selections=5,
    ),
    GuidedStepDef(
        step_id="transport_preference",
        intro="This helps us estimate travel times from the cabana.",
        question="How do you prefer to get around?",
        input_type="single_select",
        options=(
            _opt("private_driver", "Private driver"),
            _opt("tuk_tuk", "Tuk-tuk & local rides"),
            _opt("rental", "Rental car"),
            _opt("flexible", "Flexible / undecided"),
        ),
        preference_field="transport_preference",
    ),
    GuidedStepDef(
        step_id="early_starts",
        intro="Sunrise safaris and temple visits often start early.",
        question="Are early starts OK for you?",
        input_type="single_select",
        options=(
            _opt("yes", "Yes, happy to start early"),
            _opt("sometimes", "Only some days"),
            _opt("no", "Prefer late mornings"),
        ),
        preference_field="early_starts_ok",
    ),
    GuidedStepDef(
        step_id="itinerary_confirm",
        intro="I'll build a day-by-day plan from curated attractions.",
        question="Create your personalised itinerary?",
        input_type="confirm",
        options=(_opt("generate", "Plan my itinerary"),),
        allow_free_text=False,
        is_confirm=True,
        is_generate_trigger=True,
    ),
)

FEEDBACK_STEPS: tuple[GuidedStepDef, ...] = (
    GuidedStepDef(
        step_id="package_rating",
        intro="Thank you for helping Leafy Cave welcome future guests.",
        question="How was your cabana package value?",
        input_type="rating",
        options=tuple(_opt(str(i), f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)),
        preference_field="package_rating",
        allow_free_text=False,
    ),
    GuidedStepDef(
        step_id="food_rating",
        intro="Your food experience matters to us.",
        question="How was the food guidance and dining?",
        input_type="rating",
        options=tuple(_opt(str(i), f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)),
        preference_field="food_rating",
        allow_free_text=False,
    ),
    GuidedStepDef(
        step_id="itinerary_rating",
        intro="Almost done — two more quick ratings.",
        question="How accurate and helpful was your itinerary?",
        input_type="rating",
        options=tuple(_opt(str(i), f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)),
        preference_field="itinerary_rating",
        allow_free_text=False,
    ),
    GuidedStepDef(
        step_id="ai_rating",
        intro="Last rating — then you can add a comment.",
        question="How helpful was LeafyMind AI planning?",
        input_type="rating",
        options=tuple(_opt(str(i), f"{i} star{'s' if i != 1 else ''}") for i in range(1, 6)),
        preference_field="ai_helpfulness_rating",
        allow_free_text=False,
    ),
    GuidedStepDef(
        step_id="feedback_comment",
        intro="We read every note personally.",
        question="Anything else you'd like Leafy Cave to know?",
        input_type="text",
        options=(_opt("skip", "No comment — submit"),),
        allow_skip=True,
        allow_free_text=True,
        free_text_label="Your feedback (optional)",
        is_confirm=True,
    ),
)

AGENT_STEPS: dict[str, tuple[GuidedStepDef, ...]] = {
    "profile_builder": PROFILE_STEPS,
    "package_recommender": PACKAGE_STEPS,
    "food_guide": FOOD_STEPS,
    "itinerary_planner": ITINERARY_STEPS,
    "feedback_collector": FEEDBACK_STEPS,
}


def get_steps(agent_id: str) -> tuple[GuidedStepDef, ...]:
    return AGENT_STEPS.get(agent_id, ())


def get_step(agent_id: str, step_id: str) -> GuidedStepDef | None:
    for step in get_steps(agent_id):
        if step.step_id == step_id:
            return step
    return None


def get_step_index(agent_id: str, step_id: str) -> int:
    for i, step in enumerate(get_steps(agent_id)):
        if step.step_id == step_id:
            return i
    return 0


def total_steps(agent_id: str) -> int:
    return len(get_steps(agent_id))


def _clean_profile(profile: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in profile.items() if not str(k).startswith("_")}


def build_turn_payload(
    agent_id: str,
    step: GuidedStepDef,
    profile: dict[str, Any],
    prefs: dict[str, Any],
    *,
    step_index: int,
) -> dict[str, Any]:
    """Serialise a guided turn for SSE."""
    total = total_steps(agent_id)
    question = step.question
    if step.step_id == "meal_plan_confirm":
        nights = profile.get("duration_nights") or 3
        meals = int(nights) * 3
        question = (
            f"For your {nights}-night stay, we usually plan about {meals} meals "
            f"(breakfast, lunch & dinner). Does that sound right?"
        )
    if step.step_id == "profile_confirm":
        gp = GuestProfile.from_dict(profile)
        summary_lines = [
            f"Group: {gp.group_type or '—'}",
            f"Style: {gp.travel_style or '—'}",
            f"Budget: {gp.budget_tier or '—'}",
            f"Dietary: {gp.dietary_restrictions or '—'}",
            f"Nights: {gp.duration_nights or '—'}",
            f"Interests: {', '.join(gp.interests) if gp.interests else '—'}",
        ]
        question = "Your profile:\n" + "\n".join(summary_lines)

    return {
        "step_id": step.step_id,
        "intro": step.intro,
        "question": question,
        "input_type": step.input_type,
        "options": [
            {"id": o.id, "label": o.label, "description": o.description}
            for o in step.options
        ],
        "allow_skip": step.allow_skip,
        "allow_free_text": step.allow_free_text,
        "free_text_label": step.free_text_label,
        "min_selections": step.min_selections,
        "max_selections": step.max_selections,
        "is_confirm": step.is_confirm,
        "is_generate_trigger": step.is_generate_trigger,
        "progress": {"current": step_index + 1, "total": total},
        "profile_snapshot": _clean_profile(profile),
        "preferences_snapshot": dict(prefs),
    }


def apply_profile_answer(
    profile: dict[str, Any],
    step: GuidedStepDef,
    selected: list[str],
    free_text: str | None,
) -> dict[str, Any]:
    """Map guided selections into guest profile fields."""
    updated = dict(profile)
    if step.step_id == "profile_confirm":
        if "edit" in selected:
            updated["_guided_step_index"] = 0
        return updated
    if step.step_id == "contact":
        if free_text and "@" in free_text:
            from models.guest_profile import normalize_email

            email = normalize_email(free_text)
            if email:
                updated["email"] = email
        if "skip" in selected or not free_text:
            pass
        return updated
    if step.profile_field == "dietary_restrictions":
        if "none" in selected and len(selected) == 1:
            updated["dietary_restrictions"] = "none"
        else:
            labels = [s for s in selected if s != "none"]
            extra = (free_text or "").strip()
            parts = labels + ([extra] if extra else [])
            updated["dietary_restrictions"] = ", ".join(parts) if parts else "none"
        return updated
    if step.profile_field == "interests":
        updated["interests"] = [s for s in selected]
        if free_text:
            updated["interests"] = list(updated["interests"]) + [
                t.strip() for t in free_text.split(",") if t.strip()
            ]
        return updated
    if step.profile_field == "duration_nights":
        if selected:
            try:
                updated["duration_nights"] = int(selected[0])
            except ValueError:
                pass
        if free_text:
            try:
                updated["duration_nights"] = int("".join(c for c in free_text if c.isdigit())[:2] or 0)
            except ValueError:
                pass
        return updated
    if step.profile_field and selected:
        updated[step.profile_field] = selected[0]
    return updated


def apply_preference_answer(
    prefs: dict[str, Any],
    step: GuidedStepDef,
    selected: list[str],
    free_text: str | None,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Map guided selections into agent_preferences."""
    updated = dict(prefs)
    if step.step_id == "meal_plan_confirm":
        nights = int(profile.get("duration_nights") or 3)
        base = nights * 3
        if "fewer" in selected:
            updated["meal_plan_count"] = max(3, base - 3)
        elif "more" in selected:
            updated["meal_plan_count"] = base + 3
        else:
            updated["meal_plan_count"] = base
        if free_text:
            try:
                updated["meal_plan_count"] = int("".join(c for c in free_text if c.isdigit())[:2])
            except ValueError:
                pass
        return updated
    if step.preference_field == "early_starts_ok":
        mapping = {"yes": True, "sometimes": True, "no": False}
        if selected:
            updated["early_starts_ok"] = mapping.get(selected[0], True)
        return updated
    if step.preference_field and step.input_type == "multi_select":
        updated[step.preference_field] = [s for s in selected if s != "none"]
        return updated
    if step.preference_field and selected:
        val = selected[0]
        if step.input_type == "rating":
            try:
                updated[step.preference_field] = int(val)
            except ValueError:
                pass
        else:
            updated[step.preference_field] = val
    if free_text and step.step_id == "feedback_comment":
        updated["free_text_feedback"] = free_text.strip()
    return updated


def next_step_index(agent_id: str, current_index: int, step: GuidedStepDef, selected: list[str]) -> int:
    if agent_id == "profile_builder" and step.step_id == "profile_confirm" and "edit" in selected:
        return 0
    if step.is_confirm and not step.is_generate_trigger:
        return current_index
    return current_index + 1


def is_profile_complete(profile: dict[str, Any]) -> bool:
    return ProfileBuilderAgent.is_profile_complete(profile)


def is_generate_trigger(step: GuidedStepDef, selected: list[str]) -> bool:
    return step.is_generate_trigger and ("generate" in selected or "confirm" in selected)


def format_answer_label(step: GuidedStepDef, selected: list[str], free_text: str | None) -> str:
    parts = []
    for sid in selected:
        for opt in step.options:
            if opt.id == sid:
                parts.append(opt.label)
                break
        else:
            parts.append(sid)
    if free_text:
        parts.append(free_text)
    return ", ".join(parts) if parts else "Continue"
