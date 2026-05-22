"""Profile Builder agent — conversational guest preference extraction."""

import json
import logging
import re
from typing import Any

from agents.base_agent import BaseAgent
from models.guest_profile import (
    GuestProfile,
    infer_contact_preference,
    normalize_contact_preference,
    normalize_email,
    normalize_whatsapp,
)
from services.prompt_context import get_property_context

logger = logging.getLogger(__name__)

PROFILE_SYSTEM_PROMPT = """You are a warm, friendly travel concierge for Leafy Cave, a luxury nature cabana in Sri Lanka.
Your job is to gently learn about the guest's travel preferences through natural conversation — never use a form or list of questions.
Ask one question at a time. Be enthusiastic about Sri Lanka.

Through conversation, discover: travel_style, group_type, group_size, budget_tier, dietary_restrictions,
arrival_date, duration_nights, interests, fitness_level, origin_country, special_occasions.

Once you have a good picture of their trip (style, group, budget, diet, and duration), naturally ask for contact details
so Leafy Cave can send their itinerary and follow up after their stay. Example tone:
"Before I put together your full plan, I'd love to send you a copy of your itinerary and check in after your stay.
What's the best email address for you?"
Then optionally: "Would you also like updates on WhatsApp? If so, please share your number with country code (e.g. +94…)."
If they decline email or WhatsApp, accept gracefully — never pressure them or block progress.

Keep replies concise (2–4 sentences). Use plain English for international tourists."""

EXTRACTION_PROMPT = """You are a data extraction assistant. Read the conversation and extract ONLY guest travel preferences
and contact details that were clearly stated or strongly implied. Return ONLY valid JSON with any of these keys (omit unknown keys):
travel_style, group_type, group_size, budget_tier, dietary_restrictions, arrival_date, duration_nights,
interests (array of strings), fitness_level, origin_country, special_occasions,
email (string), whatsapp_number (string, include country code if given), contact_preference ("email" | "whatsapp" | "both").
If the guest declined or skipped email or WhatsApp, omit that key or set it to null.
Use null for unknown scalar fields. Do not invent values. No markdown, no explanation — JSON object only."""


class ProfileBuilderAgent(BaseAgent):
    """Builds guest profiles through warm, conversational preference gathering."""

    agent_name = "ProfileBuilderAgent"

    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:
        """Run profiling conversation turn and extract newly revealed fields."""
        user_message = self._sanitize_input(payload.get("user_message", ""))
        conversation_history = payload.get("conversation_history", [])
        current_profile = payload.get("current_profile", {})

        system = f"{PROFILE_SYSTEM_PROMPT}\n\n{get_property_context()}"
        messages = self._build_messages(system, conversation_history, user_message)
        agent_response = await self._llm.invoke_messages_direct(messages)

        updated_history = conversation_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": agent_response},
        ]
        extracted = await self.extract_profile_fields(updated_history)

        profile_model = GuestProfile.from_dict(current_profile).merge(extracted)
        updated_profile = profile_model.to_session_dict()
        # Preserve session metadata keys (e.g. _phase)
        for key, value in current_profile.items():
            if str(key).startswith("_") and key not in updated_profile:
                updated_profile[key] = value

        is_complete = self.is_profile_complete(updated_profile)

        self._log_agent_call(
            self.agent_name,
            f"user_message={user_message[:80]}",
            f"extracted_keys={list(extracted.keys())} complete={is_complete}",
        )

        return {
            "agent_response": agent_response,
            "updated_profile": updated_profile,
            "is_profile_complete": is_complete,
            "agent_used": self.agent_name,
        }

    async def extract_profile_fields(self, conversation_history: list[dict[str, Any]]) -> dict[str, Any]:
        """Parse conversation history and return validated partial profile fields."""
        transcript = "\n".join(
            f"{t.get('role', 'user').upper()}: {t.get('content', '')}"
            for t in conversation_history[-20:]
        )
        raw = await self._llm.invoke(transcript, EXTRACTION_PROMPT)
        parsed = self._parse_json_response(raw)
        return self._validate_extracted_fields(parsed)

    @staticmethod
    def is_profile_complete(profile: dict[str, Any]) -> bool:
        """Return True when all required profiling fields are present (contact fields optional)."""
        return GuestProfile.from_dict(profile).is_complete()

    def _parse_json_response(self, raw: str) -> dict[str, Any]:
        """Extract JSON object from LLM response text."""
        text = raw.strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fence:
            text = fence.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start : end + 1]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse profile extraction JSON: %s", raw[:200])
            return {}

    def _validate_extracted_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """Validate extracted fields; drop invalid contact values without blocking other fields."""
        if not data:
            return {}

        validated_contact = self._validate_contact_fields(data)
        merged = {**data, **validated_contact}
        for key in ("email", "whatsapp_number", "contact_preference"):
            if key not in validated_contact:
                merged.pop(key, None)

        try:
            model = GuestProfile.model_validate(merged, strict=False)
            confirmed: dict[str, Any] = {}
            for key in GuestProfile.model_fields:
                value = getattr(model, key)
                if value is None or value == "" or value == []:
                    continue
                if key in merged:
                    confirmed[key] = value
            return confirmed
        except Exception as exc:
            logger.warning("Profile field validation failed: %s", exc)
            return {}

    @staticmethod
    def _validate_contact_fields(data: dict[str, Any]) -> dict[str, Any]:
        """Validate email, WhatsApp, and contact preference; never raise on bad contact input."""
        result: dict[str, Any] = {}

        if "email" in data:
            email = normalize_email(data.get("email"))
            if email:
                result["email"] = email

        if "whatsapp_number" in data:
            whatsapp = normalize_whatsapp(data.get("whatsapp_number"))
            if whatsapp:
                result["whatsapp_number"] = whatsapp

        explicit_pref = None
        if "contact_preference" in data:
            explicit_pref = normalize_contact_preference(data.get("contact_preference"))
            if explicit_pref:
                result["contact_preference"] = explicit_pref

        inferred = infer_contact_preference(
            result.get("email"),
            result.get("whatsapp_number"),
            explicit_pref,
        )
        if inferred and "contact_preference" not in result:
            result["contact_preference"] = inferred

        return result
