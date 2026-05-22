"""
Feedback Collector agent — post-stay survey and structured feedback capture.

Post-stay guests also receive a branded feedback email via Gmail SMTP
(see services.email_service and services.feedback_scheduler).
"""

import json
import re
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from agents.base_agent import BaseAgent
from models.feedback import Feedback
from services.prompt_context import get_property_context

FEEDBACK_SYSTEM_PROMPT = """You are a friendly post-stay survey agent for Leafy Cave.
Your goal is to collect genuine feedback from guests who just completed their stay.
Be warm and grateful. Ask about their experience naturally — don't make it feel like a form.
Collect ratings (1-5) for: package value, food quality, itinerary accuracy, and AI helpfulness.
Ask one topic at a time across 3-4 conversational turns before wrapping up."""

FEEDBACK_EXTRACTION_PROMPT = """Extract structured feedback from this conversation.
Return ONLY valid JSON:
{
  "package_rating": 1-5 or null,
  "food_rating": 1-5 or null,
  "itinerary_rating": 1-5 or null,
  "ai_helpfulness_rating": 1-5 or null,
  "free_text_feedback": "summary string or null",
  "tags": ["positive", "value_complaint", "food_issue", "itinerary_mismatch", "ai_helpful", "ai_unhelpful"],
  "ready_to_save": true/false
}
Only set ready_to_save true if at least package_rating and one other rating are present."""

MAX_FEEDBACK_TURNS = 4


class FeedbackCollectorAgent(BaseAgent):
    """Encourages thoughtful feedback and persists structured ratings."""

    agent_name = "FeedbackCollectorAgent"

    def __init__(
        self,
        llm_service: Any,
        knowledge_base: Any,
        db: AsyncSession,
    ) -> None:
        super().__init__(llm_service, knowledge_base)
        self._db = db

    async def process(self, payload: dict[str, Any], session_context: dict[str, Any]) -> dict[str, Any]:
        """Conduct feedback conversation; extract and save when complete."""
        user_message = self._sanitize_input(payload.get("user_message", ""))
        history = payload.get("conversation_history", [])
        session_id = session_context.get("session_id")
        user_id = session_context.get("user_id")

        feedback_turns = sum(
            1 for t in history if t.get("agent_used") == self.agent_name
        )

        system = f"{FEEDBACK_SYSTEM_PROMPT}\n\n{get_property_context()}"
        messages = self._build_messages(system, history, user_message)
        agent_response = await self._llm.invoke_messages_direct(messages)

        updated_history = history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": agent_response, "agent_used": self.agent_name},
        ]

        ratings: dict[str, Any] = {}
        tags: list[str] = []
        feedback_saved = False
        flagged = False

        if feedback_turns + 1 >= MAX_FEEDBACK_TURNS or self._guest_signals_completion(user_message):
            extracted = await self._extract_feedback(updated_history)
            ratings = {
                k: extracted.get(k)
                for k in (
                    "package_rating",
                    "food_rating",
                    "itinerary_rating",
                    "ai_helpfulness_rating",
                )
                if extracted.get(k) is not None
            }
            tags = extracted.get("tags") or self._auto_tag(ratings, extracted.get("free_text_feedback"))
            flagged = any(
                (ratings.get(k) or 5) <= 2
                for k in ratings
            )

            if extracted.get("ready_to_save") and session_id and user_id:
                feedback_saved = await self._save_feedback(
                    session_id=session_id,
                    user_id=user_id,
                    ratings=ratings,
                    free_text=extracted.get("free_text_feedback"),
                    tags=tags,
                    flagged=flagged,
                )

        self._log_agent_call(
            self.agent_name,
            f"turn={feedback_turns + 1}",
            f"saved={feedback_saved} tags={tags}",
        )

        return {
            "agent_response": agent_response,
            "feedback_saved": feedback_saved,
            "ratings": ratings,
            "tags": tags,
            "flagged_for_review": flagged,
            "agent_used": self.agent_name,
        }

    async def run(self, message: str, user_id: str | None = None) -> str:
        """Backward-compatible entry point."""
        result = await self.process(
            {"user_message": message, "conversation_history": []},
            {"user_id": user_id},
        )
        return result.get("agent_response", "")

    async def _extract_feedback(self, history: list[dict[str, Any]]) -> dict[str, Any]:
        transcript = "\n".join(
            f"{t.get('role', 'user').upper()}: {t.get('content', '')}"
            for t in history[-12:]
        )
        raw = await self._llm.invoke(transcript, FEEDBACK_EXTRACTION_PROMPT)
        return self._parse_json(raw)

    async def _save_feedback(
        self,
        session_id: str,
        user_id: str,
        ratings: dict[str, Any],
        free_text: str | None,
        tags: list[str],
        flagged: bool,
    ) -> bool:
        """Persist feedback record to PostgreSQL."""
        record = Feedback(
            session_id=uuid.UUID(session_id),
            user_id=uuid.UUID(user_id),
            package_rating=ratings.get("package_rating"),
            food_rating=ratings.get("food_rating"),
            itinerary_rating=ratings.get("itinerary_rating"),
            ai_helpfulness_rating=ratings.get("ai_helpfulness_rating"),
            free_text_feedback=free_text,
            auto_tags=tags,
            flagged_for_review=flagged,
        )
        self._db.add(record)
        await self._db.flush()
        return True

    @staticmethod
    def _auto_tag(ratings: dict[str, Any], free_text: str | None) -> list[str]:
        tags: list[str] = []
        text = (free_text or "").lower()

        if all((ratings.get(k) or 0) >= 4 for k in ratings):
            tags.append("positive")
        if (ratings.get("package_rating") or 5) <= 2:
            tags.append("value_complaint")
        if (ratings.get("food_rating") or 5) <= 2:
            tags.append("food_issue")
        if (ratings.get("itinerary_rating") or 5) <= 2:
            tags.append("itinerary_mismatch")
        if (ratings.get("ai_helpfulness_rating") or 5) >= 4:
            tags.append("ai_helpful")
        elif ratings.get("ai_helpfulness_rating") is not None:
            tags.append("ai_unhelpful")

        if "food" in text and any(w in text for w in ("bad", "poor", "disappoint")):
            if "food_issue" not in tags:
                tags.append("food_issue")
        if not tags:
            tags.append("positive")
        return tags

    @staticmethod
    def _guest_signals_completion(message: str) -> bool:
        lower = message.lower()
        return any(
            phrase in lower
            for phrase in (
                "that's all",
                "thats all",
                "nothing else",
                "done",
                "finished",
                "thank you",
                "thanks",
                "bye",
            )
        )

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
            return {}
