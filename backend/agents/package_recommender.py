"""Package Recommender agent — personalised stay package suggestions."""

import asyncio
import json
import logging
import re

from typing import Any

logger = logging.getLogger(__name__)

LLM_NARRATIVE_TIMEOUT_SECONDS = 45.0



from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession



from agents.base_agent import BaseAgent

from models.guest_profile import GuestProfile

from models.package import Package

from rules.business_rules import PackageRules

from services.prompt_context import get_property_context



PACKAGE_SYSTEM_PROMPT = """You are presenting 1-2 Leafy Cave packages to a specific guest.



CRITICAL — package names:

- Use ONLY the exact package names from the candidate list (character-for-character).

- Never invent, shorten, or rename packages (e.g. do NOT say "Love Nest" — say "Love Nest Getaway").

- If the candidate is a custom/tailored package, use that exact custom name.



For each package you MUST:

1. Start with the guest's specific situation (e.g. 'As a couple celebrating your anniversary...')

2. Name exactly what they get that matters to them

3. Be honest about what is NOT included

4. Give the price clearly in USD per night

Never use generic sales language. Be specific and personal.



If the guest is a remote worker or digital nomad, emphasize the Remote Work Retreat:

mention the stable WiFi, private workspace in the cabana, full meals taken care of so they

never leave their desk hungry, and evening nature activities to decompress.



Respond with valid JSON only (no markdown fences):

{

  "narrative": "warm overview that names each package using exact candidate names",

  "recommendations": [

    {

      "package_name": "exact name from candidate list only",

      "why_this_fits": "personalized paragraph following the four rules above"

    }

  ]

}

Pick 1-2 packages from the candidate list only."""



WORKATION_TRIGGERS = frozenset(

    {

        "work",

        "remote",

        "laptop",

        "digital nomad",

        "workation",

        "work from",

        "freelance",

        "office escape",

        "wfh",

    }

)





class PackageRecommenderAgent(BaseAgent):

    """Recommends cabana packages using knowledge base, business rules, and LLM narration."""



    agent_name = "PackageRecommenderAgent"



    def __init__(

        self,

        llm_service: Any,

        knowledge_base: Any,

        db: AsyncSession,

    ) -> None:

        super().__init__(llm_service, knowledge_base)

        self._db = db

        self._rules = PackageRules()



    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:

        """Generate personalised package recommendations for the guest profile."""

        profile_data = payload.get("guest_profile", {})

        agent_preferences = payload.get("agent_preferences") or {}

        profile = (

            profile_data

            if isinstance(profile_data, GuestProfile)

            else GuestProfile.from_dict(profile_data)

        )

        profile_dict = profile.model_dump()



        result = await self._db.execute(

            select(Package).where(Package.is_active.is_(True))

        )

        all_packages = list(result.scalars().all())



        if not all_packages:

            return {

                "recommendations": [],

                "narrative": (

                    "Our cabana packages are being updated — please check back shortly "

                    "or contact Leafy Cave directly."

                ),

                "agent_used": self.agent_name,

            }



        eligible = self._eligible_packages(all_packages, profile_dict)

        pool = eligible or all_packages

        scored = self._rules.get_scored_packages(pool, profile_dict)



        strong_scored = [

            (pkg, score)

            for pkg, score in scored

            if self._rules.is_strong_match(pkg, profile_dict, score)

        ][:2]



        if strong_scored:

            narrative, why_by_name = await self._generate_llm_content(

                profile, strong_scored, agent_preferences

            )

            recommendations = self._build_recommendations(

                strong_scored, why_by_name, profile

            )

        else:

            custom_name = self._rules.build_custom_package_name(profile_dict)

            narrative, why_by_name = await self._generate_custom_llm_content(

                profile, custom_name, agent_preferences, scored

            )

            recommendations = [

                self._build_custom_recommendation(

                    custom_name, profile, why_by_name.get(custom_name), scored

                )

            ]



        narrative = self._ensure_exact_names_in_narrative(narrative, recommendations)



        self._log_agent_call(

            self.agent_name,

            f"profile={self._profile_summary(profile)[:100]}",

            f"packages={[r['package_name'] for r in recommendations]}",

        )



        return {

            "recommendations": recommendations,

            "narrative": narrative,

            "agent_used": self.agent_name,

        }



    async def run(self, message: str, user_id: str | None = None) -> str:

        """Backward-compatible entry point for the orchestrator."""

        import uuid



        from models.enums import SessionStatus

        from models.session import Session



        profile_dict: dict = {}

        if user_id:

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



    def _profile_summary(self, profile: GuestProfile) -> str:

        """Build a text summary for vector search."""

        parts = [

            f"travel_style: {profile.travel_style}",

            f"group_type: {profile.group_type}",

            f"group_size: {profile.group_size}",

            f"budget_tier: {profile.budget_tier}",

            f"duration_nights: {profile.duration_nights}",

            f"interests: {', '.join(profile.interests)}",

            f"special_occasions: {profile.special_occasions}",

        ]

        return ". ".join(p for p in parts if p and "None" not in p)



    @staticmethod

    def _eligible_packages(

        packages: list[Package], profile: dict[str, Any]

    ) -> list[Package]:

        """Pre-filter by party size and minimum stay before rules scoring."""

        size = int(profile.get("group_size") or 1)

        filtered = [p for p in packages if p.max_guests >= size]

        nights = profile.get("duration_nights")

        if nights and int(nights) >= 1:

            filtered = [p for p in filtered if p.min_nights <= int(nights)]

        return filtered



    @staticmethod

    def _is_workation_guest(profile: GuestProfile) -> bool:

        combined = " ".join(

            [

                (profile.travel_style or "").lower(),

                (profile.special_occasions or "").lower(),

                " ".join(str(i).lower() for i in (profile.interests or [])),

            ]

        )

        return any(t in combined for t in WORKATION_TRIGGERS)



    def _build_recommendations(

        self,

        candidates: list[tuple[Package, float]],

        why_by_name: dict[str, str],

        profile: GuestProfile,

    ) -> list[dict[str, Any]]:

        """Assemble structured recommendation payloads for the API response."""

        recommendations: list[dict[str, Any]] = []

        for pkg, score in candidates:

            canonical = self._rules.normalize_package_name(pkg.name) or pkg.name

            why = (

                why_by_name.get(canonical)

                or why_by_name.get(pkg.name)

                or self._fallback_why(pkg, profile, score)

            )

            recommendations.append(

                {

                    "package_name": canonical,

                    "name": canonical,

                    "package_id": str(pkg.id),

                    "tier": pkg.tier.value if hasattr(pkg.tier, "value") else str(pkg.tier),

                    "score": score,

                    "is_custom": False,

                    "price_per_night_usd": float(pkg.price_per_night_usd)

                    if pkg.price_per_night_usd

                    else None,

                    "min_nights": pkg.min_nights,

                    "why_this_fits": why,

                    "fit_reason": why,

                    "inclusions": list(pkg.inclusions or []),

                    "exclusions": list(pkg.exclusions or []),

                    "honeymoon_recommended": bool(

                        getattr(pkg, "honeymoon_recommended", False)

                    ),

                    "seasonal_note": pkg.seasonal_note,

                }

            )

        return recommendations



    def _build_custom_recommendation(

        self,

        custom_name: str,

        profile: GuestProfile,

        why: str | None,

        scored: list[tuple[Package, float]],

    ) -> dict[str, Any]:

        """Build a tailored package when no seeded offering is a strong rules match."""

        price = self._estimate_custom_price(profile, scored)

        nights = int(profile.duration_nights or 2)

        why_text = why or self._fallback_custom_why(custom_name, profile, nights)

        return {

            "package_name": custom_name,

            "name": custom_name,

            "package_id": None,

            "tier": "custom",

            "score": None,

            "is_custom": True,

            "price_per_night_usd": price,

            "min_nights": max(1, nights),

            "why_this_fits": why_text,

            "fit_reason": why_text,

            "inclusions": [

                "Private cabana stay at Leafy Cave, Wellawaya",

                "Personalised inclusions coordinated with our team",

                "Flexible meal and activity planning for your group",

            ],

            "exclusions": [

                "Final pricing confirmed after owner review",

                "External tour transport unless requested",

            ],

            "honeymoon_recommended": "love nest" in custom_name.lower(),

            "seasonal_note": None,

        }



    def _estimate_custom_price(

        self,

        profile: GuestProfile,

        scored: list[tuple[Package, float]],

    ) -> float:

        """Indicative nightly rate from budget tier or nearest scored package."""

        tier_ranges = PackageRules.BUDGET_TIER_RANGES

        tier = (profile.budget_tier or "mid_range").lower()

        low, high = tier_ranges.get(tier, tier_ranges["mid_range"])

        if scored:

            nearest = float(scored[0][0].price_per_night_usd or 0)

            if nearest > 0:

                return round(nearest, 2)

        return round((low + high) / 2, 2)



    def _fallback_custom_why(

        self, custom_name: str, profile: GuestProfile, nights: int

    ) -> str:

        group = profile.group_type or "your party"

        style = profile.travel_style or "travel"

        return (

            f"As {group} travellers seeking a {style} experience for {nights} night(s), "

            f"none of our standard packages was a perfect rules match — so we prepared "

            f"**{custom_name}**. Our team will tailor inclusions, meals, and activities "

            f"to your profile. Share any must-haves and we will confirm details with you."

        )



    def _fallback_llm_content(
        self,
        candidates: list[tuple[Package, float]],
        profile: GuestProfile,
    ) -> tuple[str, dict[str, str]]:
        """Rule-based narrative when the LLM is slow or unavailable."""
        why_by_name: dict[str, str] = {}
        names: list[str] = []
        for pkg, score in candidates:
            canonical = self._rules.normalize_package_name(pkg.name) or pkg.name
            names.append(canonical)
            why_by_name[canonical] = self._fallback_why(pkg, profile, score)
        if len(names) == 1:
            narrative = (
                f"For your stay, **{names[0]}** is our strongest match from Leafy Cave's "
                "cabana packages — see the details below."
            )
        else:
            joined = " and ".join(f"**{n}**" for n in names)
            narrative = (
                f"Here are {joined} — our best rule-matched packages for your trip profile."
            )
        return narrative, why_by_name

    def _fallback_why(self, pkg: Package, profile: GuestProfile, score: float) -> str:

        """Rule-based personalized blurb when LLM parsing fails."""

        price = float(pkg.price_per_night_usd or 0)

        parts: list[str] = []

        if profile.group_type:

            parts.append(f"As {profile.group_type} travellers")

        if profile.special_occasions:

            parts.append(f"celebrating {profile.special_occasions}")

        opener = ", ".join(parts) if parts else "For your stay"

        inclusions = ", ".join((pkg.inclusions or [])[:3])

        exclusions = ", ".join((pkg.exclusions or [])[:2])

        excluded_note = f" Note: not included — {exclusions}." if exclusions else ""

        canonical = self._rules.normalize_package_name(pkg.name) or pkg.name

        return (

            f"{opener}, **{canonical}** (match score {score:.2f}) gives you {inclusions} "

            f"at USD {price:.0f} per night.{excluded_note}"

        )



    async def _generate_llm_content(

        self,

        profile: GuestProfile,

        candidates: list[tuple[Package, float]],

        agent_preferences: dict[str, Any] | None = None,

    ) -> tuple[str, dict[str, str]]:

        """Ask the LLM for narrative and per-package why_this_fits copy."""

        candidate_lines = []

        exact_names = []

        for pkg, score in candidates:

            canonical = self._rules.normalize_package_name(pkg.name) or pkg.name

            exact_names.append(canonical)

            block = self._package_block(pkg, display_name=canonical)

            candidate_lines.append(f"{block}\n  Match score: {score:.3f}")

        candidate_text = "\n\n".join(candidate_lines)

        names_list = ", ".join(f'"{n}"' for n in exact_names)



        prefs_block = ""

        if agent_preferences:

            prefs_block = (

                f"Package preferences from conversation:\n"

                f"{json.dumps(agent_preferences, default=str)}\n\n"

            )

        workation_note = ""

        if self._is_workation_guest(profile):

            workation_note = (

                "\n\nThis guest is a remote worker / digital nomad. "

                "If Remote Work Retreat is in the candidate list, lead with it and "

                "emphasize stable WiFi, private workspace, full meals, and evening "

                "nature time to decompress (work by day, recharge in nature by evening)."

            )



        prompt = (

            f"Guest profile:\n{self._profile_summary(profile)}\n\n"

            f"{prefs_block}"

            f"ALLOWED PACKAGE NAMES (use these strings exactly in package_name and narrative): "

            f"{names_list}\n\n"

            f"Top candidate packages from Leafy Cave database "

            f"(scored, filtered, and ranked by business rules — present 1-2 only):\n"

            f"{candidate_text}\n\n"

            "Use the match scores to explain why each package is a strong fit. "

            "Reference specific profile details in every why_this_fits."

            f"{workation_note}"

        )

        system = f"{PACKAGE_SYSTEM_PROMPT}\n\n{get_property_context()}"

        try:
            raw = await asyncio.wait_for(
                self._llm.invoke(prompt, system),
                timeout=LLM_NARRATIVE_TIMEOUT_SECONDS,
            )
            return self._parse_llm_response(raw, exact_names)
        except Exception as exc:
            logger.warning(
                "Package LLM narrative failed (%s); using rule-based copy", exc
            )
            return self._fallback_llm_content(candidates, profile)



    async def _generate_custom_llm_content(

        self,

        profile: GuestProfile,

        custom_name: str,

        agent_preferences: dict[str, Any] | None,

        scored: list[tuple[Package, float]],

    ) -> tuple[str, dict[str, str]]:

        """LLM copy for a bespoke package when rules find no strong seeded match."""

        nearest_hint = ""

        if scored:

            nearest = scored[0][0]

            nearest_hint = (

                f"\nNearest standard package for reference: {nearest.name} "

                f"(score {scored[0][1]:.2f}) — do NOT recommend it; explain why we are tailoring instead."

            )



        prefs_block = ""

        if agent_preferences:

            prefs_block = (

                f"Package preferences:\n{json.dumps(agent_preferences, default=str)}\n\n"

            )



        prompt = (

            f"Guest profile:\n{self._profile_summary(profile)}\n\n"

            f"{prefs_block}"

            f"No standard Leafy Cave package was a strong rules match for this profile.{nearest_hint}\n\n"

            f"Present ONE tailored package named exactly: \"{custom_name}\"\n"

            "Explain that our team will customize inclusions, meals, and activities. "

            "Be warm and specific to their group type, travel style, and duration."

        )

        system = (

            f"{PACKAGE_SYSTEM_PROMPT}\n\n"

            "You are recommending a single CUSTOM package — use the exact custom name provided.\n\n"

            f"{get_property_context()}"

        )

        try:
            raw = await asyncio.wait_for(
                self._llm.invoke(prompt, system),
                timeout=LLM_NARRATIVE_TIMEOUT_SECONDS,
            )
            return self._parse_llm_response(raw, [custom_name])
        except Exception as exc:
            logger.warning(
                "Custom package LLM narrative failed (%s); using rule-based copy", exc
            )
            why = self._fallback_custom_why(
                custom_name, profile, int(profile.duration_nights or 2)
            )
            narrative = (
                f"Based on your profile, we prepared **{custom_name}** — "
                "a tailored Leafy Cave stay when no standard package is a perfect match."
            )
            return narrative, {custom_name: why}



    def _parse_llm_response(

        self, raw: str, allowed_names: list[str]

    ) -> tuple[str, dict[str, str]]:

        """Extract narrative and why_this_fits map from LLM JSON; normalize package names."""

        text = raw.strip()

        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)

        if fence:

            text = fence.group(1).strip()



        why_by_name: dict[str, str] = {}

        narrative = text



        try:

            parsed = json.loads(text)

            if isinstance(parsed, dict):

                narrative = str(parsed.get("narrative") or narrative)

                for item in parsed.get("recommendations") or []:

                    if not isinstance(item, dict):

                        continue

                    raw_name = str(item.get("package_name") or "").strip()

                    if not raw_name:

                        continue

                    canonical = self._rules.normalize_package_name(raw_name)

                    if not canonical and allowed_names:

                        for allowed in allowed_names:

                            if allowed.lower() in raw_name.lower():

                                canonical = allowed

                                break

                    key = canonical or raw_name

                    why_by_name[key] = str(item.get("why_this_fits") or "")

        except json.JSONDecodeError:

            pass



        return narrative, why_by_name



    @staticmethod

    def _ensure_exact_names_in_narrative(

        narrative: str, recommendations: list[dict[str, Any]]

    ) -> str:

        """Prepend explicit package names so UI/chat always shows canonical titles."""

        names = [r.get("package_name") or r.get("name") for r in recommendations]

        names = [n for n in names if n]

        if not names:

            return narrative

        prefix = "Recommended for you: **" + "** and **".join(names) + "**.\n\n"

        if any(name in narrative for name in names):

            return narrative

        return prefix + narrative



    @staticmethod

    def _package_block(pkg: Package, *, display_name: str | None = None) -> str:

        label = display_name or pkg.name

        price = float(pkg.price_per_night_usd or 0)

        inclusions = ", ".join(pkg.inclusions or [])

        exclusions = ", ".join(pkg.exclusions or [])

        honeymoon = getattr(pkg, "honeymoon_recommended", False)

        occasion = getattr(pkg, "occasion_recommended", False)

        tags = []

        if honeymoon:

            tags.append("romantic pick")

        if occasion:

            tags.append("occasion pick")

        tag_str = f" [{', '.join(tags)}]" if tags else ""

        meta = PackageRules.package_meta_text(pkg)

        meta_line = f"\n  {meta}" if meta else ""

        return (

            f"- {label} ({pkg.tier.value}, ${price}/night, min {pkg.min_nights} nights)"

            f"{tag_str}\n"

            f"  {pkg.description or ''}{meta_line}\n"

            f"  Includes: {inclusions}\n"

            f"  Not included: {exclusions}"

        )


