"""Orchestrator agent — routes guest messages through phased specialist agents."""

import asyncio
import logging
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agents.conversation_phase import ConversationPhase
from agents.feedback_collector import FeedbackCollectorAgent
from agents.food_guide import FoodGuideAgent
from agents.itinerary_planner import ItineraryPlannerAgent
from agents.package_recommender import PackageRecommenderAgent
from agents.profile_builder import ProfileBuilderAgent
from agents.session_helpers import get_or_create_active_session
from models.escalation import Escalation
from models.guest_profile import SKIP_CONTACT_PHRASES, GuestProfile
from models.session import Session
from services.knowledge_base import knowledge_base
from services.llm_provider import llm_service
from services.prompt_context import get_property_context
from services.prompt_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)

CONTACT_COLLECTION_PROMPT = (
    "I have everything I need to build your perfect Sri Lanka experience! "
    "Before I do, may I grab your email so I can send you a copy of your "
    "personalised itinerary?"
)

CONTACT_TO_RECOMMENDING = (
    "Perfect! Let me put together your personalised Leafy Cave experience now... 🌿"
)

PROFILING_COMPLETE = """
Wonderful! I now know everything I need to craft your perfect Leafy Cave 
experience. Give me just a moment while I put together your personalised 
recommendations... 🌿
""".strip()

RECOMMENDATIONS_DELIVERED = """
That's your full personalised plan! Would you like me to adjust anything — 
perhaps explore different activities, or have questions about the food?
""".strip()

ESCALATION_NOTICE = """
Great question — this one deserves a personal answer from our team. 
I've flagged this for Pramitha who will reach out to you shortly. 🙏
""".strip()

ESCALATION_RESPONSE = (
    "I want to make sure you get the best possible answer for this. "
    "I'm flagging this for Pramitha (the owner) who will personally reach out "
    "to you within a few hours. Is there anything else I can help with in the meantime?"
)

HANDOFF_ITINERARY = (
    "\n\nWonderful choices! Shall we map out a day-by-day itinerary with the best "
    "temples, waterfalls, and hidden gems near the cabana?"
)

# (reason_key, trigger phrases)
ESCALATION_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "availability",
        (
            "is it available",
            "are you available",
            "can i book for",
            "available on",
            "availability",
            "book for december",
            "book for january",
        ),
    ),
    (
        "complaint",
        (
            "not happy",
            "disappointed",
            "wrong",
            "terrible",
            "awful",
            "unacceptable",
        ),
    ),
    (
        "human_request",
        (
            "speak to someone",
            "talk to a person",
            "real person",
            "speak to a human",
            "talk to the owner",
            "human agent",
        ),
    ),
    (
        "pricing",
        (
            "can you do a discount",
            "cheaper rate",
            "lower price",
            "best price",
            "negotiate",
        ),
    ),
)

CONTACT_SKIP_EXTRA = (
    "no thanks",
    "no thank you",
    "skip",
    "prefer not",
    "rather not",
    "don't want",
    "do not want",
    "not now",
    "maybe later",
    "no email",
)


class OrchestratorAgent:
    """Phased concierge orchestrator — sole coordinator for all specialist agents."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._profile_builder = ProfileBuilderAgent(llm_service, knowledge_base)
        self._package_agent = PackageRecommenderAgent(llm_service, knowledge_base, db)
        self._food_agent = FoodGuideAgent(llm_service, knowledge_base, db)
        self._itinerary_agent = ItineraryPlannerAgent(llm_service, knowledge_base, db)
        self._feedback_agent = FeedbackCollectorAgent(llm_service, knowledge_base, db)

    async def handle(self, message: str, user_id: str | None = None) -> str:
        """Collect a full response (non-streaming) for HTTP chat endpoints."""
        if not user_id:
            chunks = []
            async for token in self._stream_fallback(message):
                chunks.append(token)
            return "".join(chunks).strip()

        session = await get_or_create_active_session(self._db, uuid.UUID(user_id))
        parts: list[str] = []
        async for chunk in self.process_message(message, session):
            parts.append(chunk.get("token", ""))
        await self._db.flush()
        return "".join(parts).strip()

    async def process_message(
        self,
        user_message: str,
        session: Session,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Process a guest message and stream response token chunks with metadata."""
        user_message = sanitize_user_input(user_message)
        if not user_message:
            async for chunk in self._yield_stream_chunks(
                "How may I help you plan your Leafy Cave stay today?",
                "OrchestratorAgent",
                session.get_phase(),
            ):
                yield chunk
            return

        escalation_reason = self._should_escalate(user_message)
        if escalation_reason:
            session.set_phase(ConversationPhase.ESCALATED.value)
            await self._record_escalation(session, escalation_reason, user_message)
            response = ESCALATION_RESPONSE
            await self._save_turn(session, user_message, response, "OrchestratorAgent")
            async for chunk in self._yield_stream_chunks(
                response,
                "OrchestratorAgent",
                ConversationPhase.ESCALATED.value,
            ):
                yield chunk
            return

        stored_phase = session.get_phase()
        phase = self._detect_phase(session, user_message)
        session.set_phase(phase)

        history = session.get_conversation_history()
        profile = session.get_guest_profile()
        session_context = {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "phase": phase,
        }

        full_response = ""
        agent_used = "OrchestratorAgent"
        handoff = ""

        if phase == ConversationPhase.GREETING.value:
            session.set_phase(ConversationPhase.PROFILING.value)
            result = await self._profile_builder.process(
                {
                    "user_message": user_message,
                    "conversation_history": history,
                    "current_profile": profile,
                },
                session_context,
            )
            full_response = result["agent_response"]
            agent_used = result.get("agent_used", "ProfileBuilderAgent")
            session.update_guest_profile(result["updated_profile"])
            if result.get("is_profile_complete"):
                full_response, agent_used = await self._begin_contact_collection(
                    session, full_response, agent_used
                )

        elif phase == ConversationPhase.PROFILING.value:
            result = await self._profile_builder.process(
                {
                    "user_message": user_message,
                    "conversation_history": history,
                    "current_profile": profile,
                },
                session_context,
            )
            full_response = result["agent_response"]
            agent_used = result.get("agent_used", "ProfileBuilderAgent")
            session.update_guest_profile(result["updated_profile"])

            if result.get("is_profile_complete"):
                full_response, agent_used = await self._begin_contact_collection(
                    session, full_response, agent_used
                )

        elif phase == ConversationPhase.CONTACT_COLLECTION.value:
            result = await self._profile_builder.process(
                {
                    "user_message": user_message,
                    "conversation_history": history,
                    "current_profile": session.get_guest_profile(),
                },
                session_context,
            )
            full_response = result["agent_response"]
            agent_used = result.get("agent_used", "ProfileBuilderAgent")
            session.update_guest_profile(result["updated_profile"])

            if self._is_contact_collection_complete(session, user_message):
                session.set_phase(ConversationPhase.RECOMMENDING.value)
                session.update_guest_profile({"_contact_complete": True})
                rec_text = await self._run_recommending_phase(
                    user_message, session, session_context
                )
                full_response = f"{full_response}\n\n{CONTACT_TO_RECOMMENDING}\n\n{rec_text}"
                agent_used = "ProfileBuilderAgent+Recommending"
                handoff = RECOMMENDATIONS_DELIVERED

        elif phase == ConversationPhase.RECOMMENDING.value:
            if self._wants_itinerary(user_message) and self._recommendations_delivered(
                session.get_guest_profile()
            ):
                session.set_phase(ConversationPhase.ITINERARY.value)
                full_response = await self._run_itinerary_phase(
                    user_message, session, session_context
                )
                agent_used = "ItineraryPlannerAgent"
            else:
                full_response = await self._run_recommending_phase(
                    user_message, session, session_context
                )
                agent_used = "PackageRecommenderAgent+FoodGuideAgent+ItineraryPlannerAgent"
                handoff = RECOMMENDATIONS_DELIVERED

        elif phase == ConversationPhase.ITINERARY.value:
            full_response = await self._run_itinerary_phase(
                user_message, session, session_context
            )
            agent_used = "ItineraryPlannerAgent"
            if not self._wants_itinerary(user_message):
                handoff = HANDOFF_ITINERARY

        elif phase == ConversationPhase.FEEDBACK.value:
            fb_result = await self._feedback_agent.process(
                {
                    "user_message": user_message,
                    "conversation_history": history,
                },
                session_context,
            )
            full_response = fb_result["agent_response"]
            agent_used = fb_result.get("agent_used", "FeedbackCollectorAgent")

        elif phase == ConversationPhase.FOLLOWUP.value:
            result = await self._profile_builder.process(
                {
                    "user_message": user_message,
                    "conversation_history": history,
                    "current_profile": session.get_guest_profile(),
                },
                session_context,
            )
            full_response = result["agent_response"]
            agent_used = result.get("agent_used", "ProfileBuilderAgent")
            session.update_guest_profile(result["updated_profile"])

        elif phase == ConversationPhase.ESCALATED.value:
            full_response = (
                f"{ESCALATION_NOTICE}\n\n"
                "I've already shared your message with Pramitha. "
                "Is there anything else about your stay I can help with while you wait?"
            )
            agent_used = "OrchestratorAgent"

        else:
            async for token in self._stream_fallback(user_message):
                yield {"token": token, "agent": "OrchestratorAgent", "phase": phase}
            return

        if handoff and handoff.strip() not in full_response:
            full_response = f"{full_response}\n\n{handoff}"

        await self._save_turn(session, user_message, full_response, agent_used)
        async for chunk in self._yield_stream_chunks(
            full_response, agent_used, session.get_phase()
        ):
            yield chunk

    async def _begin_contact_collection(
        self,
        session: Session,
        profile_response: str,
        agent_used: str,
    ) -> tuple[str, str]:
        """Move to contact collection and prompt for email (no recommending yet)."""
        profile = session.get_guest_profile()
        if self._is_contact_collection_complete(session, ""):
            session.set_phase(ConversationPhase.RECOMMENDING.value)
            session_context = {
                "session_id": str(session.id),
                "user_id": str(session.user_id),
                "phase": ConversationPhase.RECOMMENDING.value,
            }
            rec_text = await self._run_recommending_phase("", session, session_context)
            combined = f"{profile_response}\n\n{CONTACT_TO_RECOMMENDING}\n\n{rec_text}"
            return combined, f"{agent_used}+Recommending"

        session.set_phase(ConversationPhase.CONTACT_COLLECTION.value)
        session.update_guest_profile({"_contact_prompted": True})
        if CONTACT_COLLECTION_PROMPT not in profile_response:
            profile_response = f"{profile_response}\n\n{CONTACT_COLLECTION_PROMPT}"
        return profile_response, agent_used

    async def _run_recommending_phase(
        self,
        user_message: str,
        session: Session,
        session_context: dict[str, Any],
    ) -> str:
        """Run package, food, and itinerary agents in parallel; return sectioned narrative."""
        profile = GuestProfile.from_dict(session.get_guest_profile())
        payload = {"guest_profile": profile.model_dump()}

        started = time.perf_counter()
        logger.info(
            "Recommending phase: starting parallel agents session=%s",
            session.id,
        )

        package_result, food_result, itinerary_result = await asyncio.gather(
            self._package_agent.process(payload, session_context),
            self._food_agent.process(payload, session_context),
            self._itinerary_agent.process(payload, session_context),
        )

        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "Recommending phase: parallel agents completed in %.0fms session=%s",
            elapsed_ms,
            session.id,
        )

        session.update_guest_profile({
            "_last_package_recommendations": package_result.get("recommendations", []),
            "_last_food_guide": {
                "must_try": food_result.get("must_try", []),
                "safe_starter": food_result.get("safe_starter"),
                "dishes_to_avoid": food_result.get("dishes_to_avoid", []),
                "narrative": food_result.get("narrative", ""),
            },
            "_last_itinerary": {
                "itinerary": itinerary_result.get("itinerary", []),
                "total_estimated_cost_usd": itinerary_result.get("total_estimated_cost_usd", 0),
                "narrative": itinerary_result.get("narrative", ""),
                "curated_count": itinerary_result.get("curated_count", 0),
                "discovered_count": itinerary_result.get("discovered_count", 0),
                "discoveries_unavailable": itinerary_result.get("discoveries_unavailable", False),
            },
            "_recommendations_delivered": True,
        })

        sections = [
            "### Your Leafy Cave Stay\n\n"
            + (package_result.get("narrative") or "Here are stays matched to your profile."),
            "### Sri Lankan Flavours\n\n"
            + (food_result.get("narrative") or "Here is dining guidance for your trip."),
            "### Your Day-by-Day Adventure\n\n"
            + (itinerary_result.get("narrative") or "Here is a suggested rhythm for your days."),
        ]
        return "\n\n".join(sections)

    async def _run_itinerary_phase(
        self,
        user_message: str,
        session: Session,
        session_context: dict[str, Any],
    ) -> str:
        """Delegate to the itinerary planner agent."""
        profile = GuestProfile.from_dict(session.get_guest_profile())
        result = await self._itinerary_agent.process(
            {"guest_profile": profile.model_dump()},
            session_context,
        )
        session.update_guest_profile({
            "_last_itinerary": {
                "itinerary": result.get("itinerary", []),
                "total_estimated_cost_usd": result.get("total_estimated_cost_usd", 0),
                "narrative": result.get("narrative", ""),
                "curated_count": result.get("curated_count", 0),
                "discovered_count": result.get("discovered_count", 0),
                "discoveries_unavailable": result.get("discoveries_unavailable", False),
            },
        })
        return result.get("narrative", "")

    def _detect_phase(self, session: Session, user_message: str) -> str:
        """Determine concierge phase from session state and message intent."""
        lower = user_message.lower()
        profile = session.get_guest_profile()
        stored = session.get_phase()

        if stored == ConversationPhase.ESCALATED.value:
            return ConversationPhase.ESCALATED.value

        if any(w in lower for w in ("feedback", "review", "rating", "complaint", "thank you for")):
            return ConversationPhase.FEEDBACK.value

        if stored == ConversationPhase.FEEDBACK.value:
            return ConversationPhase.FEEDBACK.value

        if stored == ConversationPhase.GREETING.value:
            return ConversationPhase.GREETING.value

        if not ProfileBuilderAgent.is_profile_complete(profile):
            return ConversationPhase.PROFILING.value

        if not self._is_contact_collection_complete(session, user_message):
            return ConversationPhase.CONTACT_COLLECTION.value

        if self._wants_itinerary(user_message):
            return ConversationPhase.ITINERARY.value

        if any(
            w in lower
            for w in ("clarify", "change my", "actually", "instead", "prefer", "update my")
        ):
            return ConversationPhase.FOLLOWUP.value

        if stored == ConversationPhase.ITINERARY.value:
            return ConversationPhase.ITINERARY.value

        if stored == ConversationPhase.CONTACT_COLLECTION.value:
            return ConversationPhase.CONTACT_COLLECTION.value

        if stored == ConversationPhase.RECOMMENDING.value:
            if self._wants_itinerary(user_message) and self._recommendations_delivered(profile):
                return ConversationPhase.ITINERARY.value
            return ConversationPhase.RECOMMENDING.value

        return ConversationPhase.RECOMMENDING.value

    @staticmethod
    def _wants_itinerary(user_message: str) -> bool:
        lower = user_message.lower()
        return any(
            w in lower
            for w in (
                "itinerary",
                "day trip",
                "day-by-day",
                "schedule",
                "plan my days",
                "activities",
                "what to do each day",
                "daily plan",
            )
        )

    @staticmethod
    def _recommendations_delivered(profile: dict[str, Any]) -> bool:
        return bool(profile.get("_recommendations_delivered"))

    def _is_contact_collection_complete(
        self, session: Session, user_message: str
    ) -> bool:
        """True when email/WhatsApp collected or guest declined contact."""
        profile = session.get_guest_profile()
        if profile.get("_contact_complete") or profile.get("_contact_skipped"):
            return True
        if profile.get("email") or profile.get("whatsapp_number"):
            return True
        if user_message and self._is_contact_skip(user_message):
            session.update_guest_profile({"_contact_skipped": True})
            return True
        return False

    @staticmethod
    def _is_contact_skip(user_message: str) -> bool:
        lower = user_message.lower().strip()
        if lower in SKIP_CONTACT_PHRASES:
            return True
        return any(phrase in lower for phrase in CONTACT_SKIP_EXTRA)

    def _should_escalate(self, user_message: str) -> str | None:
        """Return escalation reason key if message should be escalated, else None."""
        lower = user_message.lower()
        for reason, triggers in ESCALATION_RULES:
            if any(trigger in lower for trigger in triggers):
                return reason
        return None

    async def _record_escalation(
        self,
        session: Session,
        reason: str,
        user_message: str,
    ) -> None:
        """Persist escalation for owner follow-up."""
        record = Escalation(
            session_id=session.id,
            reason=reason,
            user_message=user_message[:4000],
        )
        self._db.add(record)
        await self._db.flush()
        logger.info(
            "Escalation recorded session=%s reason=%s",
            session.id,
            reason,
        )

    async def _save_turn(
        self,
        session: Session,
        user_message: str,
        agent_response: str,
        agent_used: str,
    ) -> None:
        """Persist the latest user/assistant turn on the session."""
        session.append_turn("user", user_message, agent_used=None)
        session.append_turn("assistant", agent_response, agent_used=agent_used)
        logger.debug("Saved turn session=%s agent=%s", session.id, agent_used)

    async def _yield_stream_chunks(
        self,
        text: str,
        agent: str,
        phase: str,
    ) -> AsyncGenerator[dict[str, str], None]:
        """Stream text in word chunks with agent/phase metadata."""
        if not text:
            return
        words = text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"token": token, "agent": agent, "phase": phase}

    async def _stream_fallback(self, user_message: str) -> AsyncGenerator[str, None]:
        """General concierge response when no session is available."""
        system = (
            f"You are LeafyMind, the warm AI concierge for Leafy Cave, Sri Lanka.\n"
            f"{get_property_context()}\n"
            "Answer briefly in plain English suitable for international tourists."
        )
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user_message),
        ]
        async for token in llm_service.stream_invoke_with_messages(messages):
            yield token


# Backward-compatible alias
Orchestrator = OrchestratorAgent
