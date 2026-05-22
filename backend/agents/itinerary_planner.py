"""Itinerary Planner agent — day-by-day Sri Lanka nature and culture itineraries."""

import calendar
import json
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from agents.schemas import DayActivity, DayPlan
from config import settings
from models.attraction import Attraction
from models.guest_profile import GuestProfile
from rules.business_rules import AttractionRules
from services.attraction_data_layer import AttractionDataLayer
from services.distance_calculator import distance_calculator
from services.prompt_context import get_cultural_guidelines, get_property_context

ITINERARY_SYSTEM_PROMPT = """You are an expert Sri Lanka travel planner specializing in nature and cultural experiences near Leafy Cave cabana in Wellawaya.
Create practical, day-by-day itineraries that balance activity with relaxation.
Always include realistic travel times and costs.

You have two types of attractions:
CURATED: verified by the Leafy Cave team — always prioritize these. Label as "✓ Verified by Leafy Cave".
DISCOVERED: found from public databases (OpenTripMap) — include only when provided as gap-fillers. Label as "🔍 Nearby Discovery".

Never invent attractions outside the CURATED and DISCOVERED lists provided.
For each day, suggest a morning activity, afternoon activity, and evening experience at the cabana.
Use plain English for international tourists. Be warm and specific.

For Remote Work Retreat guests: weekday plans keep mornings/afternoons free for focused work at the cabana;
schedule easy nearby evening outings (lakes, reservoir walks). Reserve one weekend day for a bigger
adventure activity (hiking, adventure park) when listed in the plan."""

REMOTE_WORK_RETREAT = "Remote Work Retreat"


class ItineraryPlannerAgent(BaseAgent):
    """Plans culturally respectful day itineraries near Leafy Cave."""

    agent_name = "ItineraryPlannerAgent"

    def __init__(
        self,
        llm_service: Any,
        knowledge_base: Any,
        db: AsyncSession,
    ) -> None:
        super().__init__(llm_service, knowledge_base)
        self._db = db
        self._attractions = AttractionDataLayer(db)
        self._rules = AttractionRules()

    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:
        """Generate a day-by-day itinerary from rules-filtered curated data, then OpenTripMap gaps."""
        profile_data = payload.get("guest_profile", {})
        agent_preferences = payload.get("agent_preferences") or {}
        profile = (
            profile_data
            if isinstance(profile_data, GuestProfile)
            else GuestProfile.from_dict(profile_data)
        )
        profile_dict = profile.model_dump()

        fitness = (profile.fitness_level or "moderate").lower()
        duration = int(profile.duration_nights or 3)

        # 1. Load verified attractions from PostgreSQL
        all_attractions = await self._attractions.list_all(limit=50)

        # 2–3. Rules filters before any external API
        filtered = self._rules.filter_by_fitness(all_attractions, fitness)
        filtered = self._rules.filter_by_duration(filtered, duration)
        filtered = self._attractions.apply_suitability_filters(filtered, profile_dict)
        filtered = self._rules.filter_seasonal(filtered, profile.arrival_date)

        workation_mode = self._is_remote_work_retreat(profile_dict)
        workation_plan: dict[str, list[Attraction]] | None = None

        # 4. Remote Work Retreat: weekday evenings + weekend adventure
        if workation_mode:
            workation_plan = self._rules.get_workation_attractions(filtered)
            curated = (
                workation_plan["weekday_recommended"]
                + workation_plan["weekend_optional"][:1]
            )
            day_groups = self._build_workation_day_groups(
                duration,
                workation_plan["weekday_recommended"],
                workation_plan["weekend_optional"],
            )
        else:
            curated = sorted(
                filtered, key=lambda a: float(a.distance_km_from_cabana or 999)
            )[:10]
            attraction_ids = [str(a.id) for a in curated]
            day_groups = await self._attractions.optimize_day_routes(
                attraction_ids, duration, fitness_level=fitness
            )

        # 5. Seasonal warnings for narrative
        arrival_month = self._arrival_month(profile.arrival_date)
        seasonal_warnings = self._rules.flag_seasonal_warnings(filtered, arrival_month)

        # 6. OpenTripMap only after rules filtering, for gaps
        discovered, discoveries_loaded = await self._attractions.fetch_discoveries_for_gaps(
            profile_dict, curated
        )

        itinerary = self._build_day_plans(
            day_groups, profile, discovered, workation_mode=workation_mode
        )
        total_cost = sum(day.estimated_day_cost_usd for day in itinerary)
        attraction_context = self._format_attractions_for_prompt(
            curated, discovered, day_groups, workation_mode=workation_mode
        )

        prefs_json = json.dumps(agent_preferences, default=str) if agent_preferences else "none"
        warnings_block = ""
        if seasonal_warnings:
            warnings_block = (
                "\n\nSeasonal advisories (you MUST weave these into the narrative):\n"
                + "\n".join(f"- {w}" for w in seasonal_warnings)
            )

        workation_block = ""
        if workation_mode:
            workation_block = (
                "\n\nThis guest is on the Remote Work Retreat package. "
                "Structure the plan as: weekday evenings at easy nearby places "
                "(Handapanagala Lake, Alikota Ara Reservoir), and one weekend day "
                "for a bigger adventure. Keep weekday mornings/afternoons for cabana work time."
            )

        prompt = (
            f"Guest profile (Profile Builder):\n"
            f"- Fitness: {profile.fitness_level}\n"
            f"- Group: {profile.group_type} ({profile.group_size} guests)\n"
            f"- Interests: {', '.join(profile.interests)}\n"
            f"- Stay: {duration} nights\n"
            f"- Base: {settings.cabana_name}\n"
            f"- Package context: {self._package_label(profile_dict)}\n\n"
            f"Itinerary preferences from conversation:\n{prefs_json}\n\n"
            f"Attraction data (use ONLY these — curated first, discoveries for gaps only):\n"
            f"{attraction_context}\n\n"
            "Write a narrative day-by-day itinerary following the groupings. "
            "Clearly label each attraction as Verified (curated) or Nearby Discovery (discovered). "
            "Include travel times from the cabana and realistic costs."
            f"{workation_block}{warnings_block}"
        )
        system = (
            f"{ITINERARY_SYSTEM_PROMPT}\n\n"
            f"{get_property_context()}\n{get_cultural_guidelines()}"
        )
        narrative = await self._llm.invoke(prompt, system)

        if seasonal_warnings:
            advisory = " ".join(seasonal_warnings)
            narrative = f"{advisory}\n\n{narrative}"

        has_otm_key = bool(settings.opentripmap_api_key.strip())
        discoveries_unavailable = has_otm_key and discoveries_loaded and not discovered

        self._log_agent_call(
            self.agent_name,
            f"nights={duration} curated={len(curated)} discovered={len(discovered)} "
            f"workation={workation_mode}",
            f"days={len(itinerary)} cost=${total_cost:.0f}",
        )

        return {
            "itinerary": [day.model_dump() for day in itinerary],
            "total_estimated_cost_usd": round(total_cost, 2),
            "narrative": narrative,
            "curated_count": len(curated),
            "discovered_count": len(discovered),
            "discoveries_unavailable": discoveries_unavailable,
            "seasonal_warnings": seasonal_warnings,
            "workation_itinerary": workation_mode,
            "agent_used": self.agent_name,
        }

    async def run(self, message: str, user_id: str | None = None) -> str:
        """Backward-compatible entry point."""
        profile_dict: dict = {}
        if user_id:
            import uuid
            from sqlalchemy import select
            from models.enums import SessionStatus
            from models.session import Session

            result = await self._db.execute(
                select(Session).where(
                    Session.user_id == uuid.UUID(user_id),
                    Session.status == SessionStatus.ACTIVE,
                )
            )
            session = result.scalar_one_or_none()
            if session:
                profile_dict = session.get_guest_profile()

        result = await self.process({"guest_profile": profile_dict}, {})
        return result.get("narrative", "")

    @staticmethod
    def _arrival_month(arrival_date: str | None) -> str:
        if not arrival_date:
            return ""
        try:
            arrival = datetime.fromisoformat(arrival_date.replace("Z", "+00:00"))
            return calendar.month_name[arrival.month]
        except ValueError:
            return ""

    @staticmethod
    def _is_remote_work_retreat(profile: dict[str, Any]) -> bool:
        selected = str(profile.get("selected_package") or "")
        if REMOTE_WORK_RETREAT in selected:
            return True
        if (profile.get("travel_style") or "").lower() == "workation":
            return True
        recommendations = profile.get("_last_package_recommendations") or []
        if recommendations and isinstance(recommendations[0], dict):
            name = recommendations[0].get("package_name") or recommendations[0].get("name")
            if name == REMOTE_WORK_RETREAT:
                return True
        combined = " ".join(
            [
                (profile.get("special_occasions") or "").lower(),
                " ".join(str(i).lower() for i in (profile.get("interests") or [])),
            ]
        )
        work_triggers = ("workation", "remote work", "digital nomad", "work from")
        return any(t in combined for t in work_triggers)

    @staticmethod
    def _package_label(profile: dict[str, Any]) -> str:
        if ItineraryPlannerAgent._is_remote_work_retreat(profile):
            return REMOTE_WORK_RETREAT
        selected = profile.get("selected_package")
        if selected:
            return str(selected)
        recommendations = profile.get("_last_package_recommendations") or []
        if recommendations and isinstance(recommendations[0], dict):
            return str(
                recommendations[0].get("package_name")
                or recommendations[0].get("name")
                or "not yet chosen"
            )
        return "not yet chosen"

    @staticmethod
    def _build_workation_day_groups(
        duration_nights: int,
        weekday: list[Attraction],
        weekend: list[Attraction],
    ) -> list[list[Attraction]]:
        """Weekday evenings = easy nearby; final day = weekend adventure."""
        num_days = max(1, min(int(duration_nights or 1), 14))
        days: list[list[Attraction]] = [[] for _ in range(num_days)]

        if weekend:
            days[-1] = [weekend[0]]

        evening_days = num_days - 1 if weekend else num_days
        for i in range(evening_days):
            if weekday:
                days[i] = [weekday[i % len(weekday)]]

        return [day for day in days if day]

    def _build_day_plans(
        self,
        day_groups: list[list[Attraction]],
        profile: GuestProfile,
        discovered: list[dict[str, Any]],
        *,
        workation_mode: bool = False,
    ) -> list[DayPlan]:
        """Convert day groups into DayPlan structures; weave in discoveries for gaps."""
        plans: list[DayPlan] = []
        disc_idx = 0
        num_days = len(day_groups)

        for day_num, group in enumerate(day_groups, start=1):
            is_adventure_day = workation_mode and day_num == num_days and group
            att = group[0] if group else None
            att2 = group[1] if len(group) > 1 else None

            if workation_mode and att and not is_adventure_day:
                morning_activity = None
                afternoon_activity = DayActivity(
                    time_of_day="afternoon",
                    attraction_name="Leafy Cave cabana",
                    description=(
                        "Focused remote work block — private desk, stable WiFi, "
                        "and meals served at your workspace."
                    ),
                    estimated_cost_usd=0.0,
                    source="curated",
                )
                dist = float(att.distance_km_from_cabana or 0)
                evening_text = (
                    f"Evening outing — {att.name} ({dist:.0f} km from cabana): "
                    f"{(att.description or '')[:160]}. "
                    "Return to Leafy Cave for bonfire, swing, and rest."
                )
                theme = "Work day with evening nature break"
            elif is_adventure_day and att:
                morning_activity = self._curated_to_activity(att, "morning")
                afternoon_activity = (
                    self._curated_to_activity(att2, "afternoon") if att2 else None
                )
                evening_text = (
                    "Return to Leafy Cave for dinner, bonfire, and rest after "
                    "your weekend adventure"
                )
                theme = "Weekend adventure day"
            else:
                morning_att = att
                afternoon_att = att2
                morning_activity = (
                    self._curated_to_activity(morning_att, "morning")
                    if morning_att
                    else None
                )
                afternoon_activity = (
                    self._curated_to_activity(afternoon_att, "afternoon")
                    if afternoon_att
                    else None
                )
                evening_activity = None
                theme = self._day_theme(group)

            if afternoon_activity is None and disc_idx < len(discovered):
                place = discovered[disc_idx]
                disc_idx += 1
                afternoon_activity = self._discovered_to_activity(place, "afternoon")

            day_cost = sum(float(a.entry_fee_usd or 0) for a in group)
            if not (workation_mode and att and not is_adventure_day):
                evening_text = (
                    "Return to Leafy Cave for dinner, herbal tea, and rest under the stars"
                )

            plans.append(
                DayPlan(
                    day_number=day_num,
                    theme=theme,
                    morning=morning_activity,
                    afternoon=afternoon_activity,
                    evening=evening_text,
                    estimated_day_cost_usd=round(day_cost, 2),
                )
            )

        for day in plans:
            if disc_idx >= len(discovered):
                break
            if day.afternoon is None:
                place = discovered[disc_idx]
                disc_idx += 1
                day.afternoon = self._discovered_to_activity(place, "afternoon")

        if not plans:
            plans.append(
                DayPlan(
                    day_number=1,
                    theme="Relaxation at the cabana",
                    evening="Enjoy Leafy Cave grounds, dinner, and stargazing",
                )
            )
        return plans

    def _curated_to_activity(self, att: Attraction, time_of_day: str) -> DayActivity:
        dist = float(att.distance_km_from_cabana or 0)
        travel = distance_calculator.estimate_travel_time(dist) if dist else None
        return DayActivity(
            time_of_day=time_of_day,
            attraction_name=att.name,
            description=(att.description or "")[:300],
            estimated_cost_usd=float(att.entry_fee_usd) if att.entry_fee_usd else 0.0,
            duration_hours=float(att.estimated_duration_hours)
            if att.estimated_duration_hours
            else None,
            source="curated",
            distance_km=dist if dist else None,
            travel_time_formatted=travel["formatted"] if travel else None,
            image_url=None,
            tips=att.tips,
            kinds=att.category.value,
        )

    def _discovered_to_activity(self, place: dict[str, Any], time_of_day: str) -> DayActivity:
        travel = place.get("travel_time") or {}
        return DayActivity(
            time_of_day=time_of_day,
            attraction_name=place.get("name", "Nearby attraction"),
            description=(place.get("description") or "")[:300],
            estimated_cost_usd=None,
            duration_hours=None,
            source="discovered",
            distance_km=place.get("distance_km"),
            travel_time_formatted=travel.get("formatted"),
            image_url=place.get("image_url"),
            tips=None,
            kinds=place.get("kinds"),
        )

    def _day_theme(self, group: list) -> str:
        if not group:
            return "Cabana relaxation"
        categories = {a.category.value for a in group}
        if "wildlife" in categories:
            return "Wildlife and nature"
        if "waterfall" in categories:
            return "Waterfalls and scenery"
        if "temple" in categories or "cultural" in categories:
            return "Culture and heritage"
        return "Exploring the hill country"

    def _format_attractions_for_prompt(
        self,
        curated: list[Attraction],
        discovered: list[dict[str, Any]],
        day_groups: list[list[Attraction]],
        *,
        workation_mode: bool = False,
    ) -> str:
        lines = ["=== CURATED (✓ Verified by Leafy Cave) ==="]
        for att in curated:
            fee = float(att.entry_fee_usd or 0)
            dist = float(att.distance_km_from_cabana or 0)
            travel = distance_calculator.estimate_travel_time(dist) if dist else {}
            lines.append(
                f"- {att.name} [{att.category.value}]: {dist}km, "
                f"{travel.get('formatted', 'n/a')}, ${fee} entry, "
                f"fitness={att.fitness_level_required.value}. {att.description or ''}"
            )

        lines.append("\n=== DISCOVERED (🔍 Nearby Discovery — gap-fill only) ===")
        if discovered:
            for place in discovered:
                dist = place.get("distance_km")
                travel = (place.get("travel_time") or {}).get("formatted", "n/a")
                lines.append(
                    f"- {place.get('name')} [{place.get('kinds', '')}]: {dist}km, "
                    f"{travel}. {place.get('description', '')}"
                )
        else:
            lines.append("- (none — verified attractions cover this guest)")

        if workation_mode:
            lines.append(
                "\nWorkation layout: weekday evenings = easy nearby curated spots; "
                "final day = one bigger adventure activity."
            )

        lines.append("\nSuggested day groupings (curated only):")
        for i, group in enumerate(day_groups, 1):
            names = ", ".join(a.name for a in group) or "rest day at cabana"
            lines.append(f"  Day {i}: {names}")
        return "\n".join(lines)
