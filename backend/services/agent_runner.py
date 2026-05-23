"""Execute specialist agents against Agent Hub threads with streaming events."""



import logging

import uuid

from collections.abc import AsyncGenerator

from typing import Any



from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession



from agents.feedback_collector import FeedbackCollectorAgent

from agents.food_guide import FoodGuideAgent

from agents.guided_steps import GUIDED_AGENTS

from agents.itinerary_planner import ItineraryPlannerAgent

from agents.orchestrator import OrchestratorAgent

from agents.package_recommender import PackageRecommenderAgent

from agents.profile_builder import ProfileBuilderAgent

from agents.registry import get_agent

from api.session_access import create_new_session

from models.agent_message import AgentMessage

from models.agent_thread import AgentThread

from models.enums import AgentThreadStatus

from models.guest_profile import GuestProfile

from models.session import Session

from models.user import User

from services.guided_flow import GuidedFlowService

from services.hub_feedback import maybe_complete_optional_agent

from services.journey_service import JourneyService

from services.knowledge_base import knowledge_base

from services.llm_provider import llm_service

from services.specialist_interview import OPTIONAL_PLANNING_AGENTS, SpecialistInterviewService



logger = logging.getLogger(__name__)





def _history_from_messages(messages: list[AgentMessage]) -> list[dict[str, Any]]:

    """Convert persisted messages to agent conversation history."""

    history: list[dict[str, Any]] = []

    for msg in messages:

        if msg.role in ("user", "assistant"):

            entry: dict[str, Any] = {"role": msg.role, "content": msg.content}

            if msg.agent_id and msg.role == "assistant":

                entry["agent_used"] = msg.agent_id

            history.append(entry)

    return history





def _profile_completeness(profile: dict[str, Any]) -> int:

    """Return 0–100 profile completeness score."""

    if ProfileBuilderAgent.is_profile_complete(profile):

        return 100

    model = GuestProfile.from_dict(profile)

    fields = [

        model.travel_style,

        model.group_type,

        model.budget_tier,

        model.dietary_restrictions is not None,

        model.duration_nights,

    ]

    filled = sum(1 for item in fields if item)

    return int((filled / len(fields)) * 100) if fields else 0





async def _stream_text(text: str, agent_id: str) -> AsyncGenerator[dict[str, Any], None]:

    """Yield word-level token events."""

    if not text:

        return

    words = text.split(" ")

    for index, word in enumerate(words):

        token = word + (" " if index < len(words) - 1 else "")

        yield {"type": "token", "token": token, "agent": agent_id}





class AgentRunner:

    """Runs a single agent turn for an Agent Hub thread."""



    def __init__(self, db: AsyncSession) -> None:

        self._db = db

        self._profile_agent = ProfileBuilderAgent(llm_service, knowledge_base)

        self._package_agent = PackageRecommenderAgent(llm_service, knowledge_base, db)

        self._food_agent = FoodGuideAgent(llm_service, knowledge_base, db)

        self._itinerary_agent = ItineraryPlannerAgent(llm_service, knowledge_base, db)

        self._feedback_agent = FeedbackCollectorAgent(llm_service, knowledge_base, db)

        self._interview = SpecialistInterviewService()

        self._guided = GuidedFlowService()



    async def process_message(

        self,

        thread: AgentThread,

        user: User,

        user_message: str,

        *,

        guided_response: dict[str, Any] | None = None,

    ) -> AsyncGenerator[dict[str, Any], None]:

        """Stream agent events for one guest message."""

        agent_def = get_agent(thread.agent_id)

        if agent_def is None:

            yield {"type": "error", "message": "Unknown agent"}

            return



        prior_messages = list(thread.messages or [])

        profile = thread.get_guest_profile()

        ctx = dict(thread.context or {})

        session_context = {

            "thread_id": str(thread.id),

            "user_id": str(user.id),

            "agent_id": thread.agent_id,

            "session_id": ctx.get("feedback_session_id"),

        }



        step_id = None

        selected: list[str] = []

        free_text: str | None = None

        if guided_response:

            step_id = guided_response.get("step_id")

            selected = list(guided_response.get("selected") or [])

            free_text = guided_response.get("free_text")



        user_content = user_message

        if guided_response and selected:

            from agents.guided_steps import format_answer_label, get_step



            step_def = get_step(thread.agent_id, step_id or "")

            if step_def:

                user_content = format_answer_label(step_def, selected, free_text) or user_message



        user_msg = AgentMessage(

            thread_id=thread.id,

            role="user",

            content=user_content,

            agent_id=thread.agent_id,

        )

        self._db.add(user_msg)



        full_response = ""

        artifacts: dict[str, Any] = {}

        tool_events: list[dict[str, Any]] = []

        agent_label = agent_def.name

        guided_turn: dict[str, Any] | None = None



        try:

            if thread.agent_id == "concierge":

                async for event in self._run_concierge(

                    thread, user, user_message, tool_events

                ):

                    if event.get("type") == "token":

                        full_response += event.get("token", "")

                    elif event.get("type") == "artifact":

                        artifacts = event.get("data", artifacts)

                    yield event

                agent_label = "Concierge"



            elif thread.agent_id in GUIDED_AGENTS:

                flow_result = self._guided.process_answer(

                    thread,

                    step_id=step_id,

                    selected=selected,

                    free_text=free_text,

                    raw_message=user_message,

                )

                profile = flow_result.profile or profile

                full_response = flow_result.assistant_content

                guided_turn = flow_result.guided_turn



                if flow_result.guided_turn:

                    ctx = dict(thread.context or {})

                    ctx["last_guided_turn"] = flow_result.guided_turn

                    thread.context = ctx



                if thread.agent_id == "profile_builder":

                    completeness = _profile_completeness(profile)

                    is_complete = flow_result.profile_complete

                    artifacts = {

                        "profile": {

                            k: v for k, v in profile.items() if not str(k).startswith("_")

                        },

                        "completeness": completeness,

                        "is_complete": is_complete,

                    }

                    thread.set_artifacts(artifacts)

                    yield {"type": "artifact", "kind": "profile", "data": artifacts}



                elif thread.agent_id == "feedback_collector" and flow_result.survey_complete:

                    saved = await self._save_guided_feedback(

                        thread, user, flow_result.preferences or {}

                    )

                    artifacts = {

                        "survey_complete": True,

                        "ratings": flow_result.feedback_ratings,

                        "feedback_saved": saved,

                    }

                    thread.set_artifacts(artifacts)

                    thread.status = AgentThreadStatus.COMPLETED

                    yield {"type": "artifact", "kind": "feedback", "data": artifacts}



                if flow_result.guided_turn:

                    yield {"type": "guided_turn", "data": flow_result.guided_turn}



                if flow_result.ready_to_generate and thread.agent_id in OPTIONAL_PLANNING_AGENTS:
                    ctx = dict(thread.context or {})
                    ctx.pop("last_guided_turn", None)
                    thread.context = ctx
                    prefs = thread.get_agent_preferences()

                    profile_dump = GuestProfile.from_dict(profile).model_dump()

                    async for event in self._generate_planning_output(

                        thread,

                        user,

                        profile_dump,

                        prefs,

                        session_context,

                        tool_events,

                        agent_label,

                    ):

                        if event.get("type") == "token":

                            full_response += event.get("token", "")

                        elif event.get("type") == "artifact":
                            kind = event.get("kind")
                            data = event.get("data") or {}
                            if kind == "food":
                                artifacts = {"food": data}
                            elif kind == "packages":
                                artifacts = {"packages": data}
                            elif kind == "itinerary":
                                artifacts = {"itinerary": data}
                            else:
                                artifacts = data

                        yield event

                elif full_response.strip():

                    async for event in _stream_text(full_response, agent_label):

                        yield event



            else:

                yield {"type": "error", "message": "Agent not implemented"}

                return



            saved_artifacts = dict(thread.get_artifacts() or {})
            if artifacts:
                saved_artifacts.update(artifacts)
            if guided_turn:
                saved_artifacts["guided_turn"] = guided_turn

            assistant_msg = AgentMessage(

                thread_id=thread.id,

                role="assistant",

                content=full_response or (guided_turn or {}).get("question", ""),

                agent_id=thread.agent_id,

                tool_events=tool_events,

                artifacts=saved_artifacts,

            )

            self._db.add(assistant_msg)

            await self._db.flush()



            journey = await JourneyService(self._db).get_journey(user.id)

            yield {

                "type": "done",

                "thread": {

                    "id": str(thread.id),

                    "agent_id": thread.agent_id,

                    "title": thread.title,

                    "status": thread.status.value,

                    "artifacts": thread.get_artifacts(),

                    "guest_profile": thread.get_guest_profile(),

                    "guided_turn": (thread.context or {}).get("last_guided_turn"),

                },

                "journey": journey,

            }

        except Exception as exc:

            logger.exception("Agent run failed thread=%s agent=%s", thread.id, thread.agent_id)

            await self._db.rollback()

            detail = str(exc).lower()

            if "api_key" in detail or "authentication" in detail or "401" in detail:

                message = (

                    "The AI service could not authenticate. Check GROQ_API_KEY in your .env file."

                )

            elif "rate limit" in detail or "429" in detail:

                message = "The AI service is busy. Please wait a moment and try again."

            else:

                message = "Something went wrong. Please try again."

            yield {"type": "error", "message": message}



    async def _save_guided_feedback(

        self,

        thread: AgentThread,

        user: User,

        prefs: dict[str, Any],

    ) -> bool:

        """Persist structured ratings from guided feedback flow."""

        session_id = (thread.context or {}).get("feedback_session_id")

        if not session_id:

            return False

        ratings = {

            k: prefs.get(k)

            for k in (

                "package_rating",

                "food_rating",

                "itinerary_rating",

                "ai_helpfulness_rating",

            )

            if prefs.get(k) is not None

        }

        if len(ratings) < 2:

            return False

        tags = FeedbackCollectorAgent._auto_tag(ratings, prefs.get("free_text_feedback"))

        flagged = any((ratings.get(k) or 5) <= 2 for k in ratings)

        return await self._feedback_agent._save_feedback(

            session_id=session_id,

            user_id=str(user.id),

            ratings=ratings,

            free_text=prefs.get("free_text_feedback"),

            tags=tags,

            flagged=flagged,

        )



    async def _generate_planning_output(

        self,

        thread: AgentThread,

        user: User,

        profile_dump: dict[str, Any],

        prefs: dict[str, Any],

        session_context: dict[str, Any],

        tool_events: list[dict[str, Any]],

        agent_label: str,

    ) -> AsyncGenerator[dict[str, Any], None]:

        """Run package/food/itinerary generation after guided interview completes."""

        agent_id = thread.agent_id

        tool_name = {

            "package_recommender": ("search_packages", "Matching cabana packages…", "Packages ready"),

            "food_guide": ("search_food", "Curating Sri Lankan flavours…", "Food guide ready"),

            "itinerary_planner": ("plan_itinerary", "Mapping your adventures…", "Itinerary ready"),

        }[agent_id]

        tool_key, tool_start_label, tool_end_label = tool_name



        yield {"type": "tool_start", "tool": tool_key, "label": tool_start_label}

        tool_events.append({"tool": tool_key, "status": "started"})

        payload = {

            "guest_profile": profile_dump,

            "agent_preferences": prefs,

        }

        artifact_payload: dict[str, Any] = {}

        artifact_kind = "packages"

        artifacts: dict[str, Any] = {}

        full_response = ""

        try:

            if agent_id == "package_recommender":

                result = await self._package_agent.process(payload, session_context)

                artifact_payload = {

                    "recommendations": result.get("recommendations", []),

                    "narrative": result.get("narrative", ""),

                }

                full_response = (

                    artifact_payload["narrative"]

                    or "Here are packages matched to your trip."

                )

                artifact_kind = "packages"

                artifacts = {"packages": artifact_payload}

            elif agent_id == "food_guide":

                result = await self._food_agent.process(payload, session_context)

                full_response = result.get("narrative") or "Here is your personalised food guide."

                artifact_payload = {

                    "must_try": result.get("must_try", []),

                    "safe_starter": result.get("safe_starter"),

                    "dishes_to_avoid": result.get("dishes_to_avoid", []),

                    "narrative": full_response,

                }

                artifact_kind = "food"

                artifacts = {"food": artifact_payload}

            else:

                result = await self._itinerary_agent.process(payload, session_context)

                full_response = result.get("narrative") or "Here is your day-by-day adventure plan."

                artifact_payload = {

                    "itinerary": result.get("itinerary", []),

                    "total_estimated_cost_usd": result.get("total_estimated_cost_usd", 0),

                    "narrative": full_response,

                    "curated_count": result.get("curated_count", 0),

                    "discovered_count": result.get("discovered_count", 0),

                }

                artifact_kind = "itinerary"

                artifacts = {"itinerary": artifact_payload}

        except Exception as exc:

            logger.exception(

                "Planning generation failed thread=%s agent=%s",

                thread.id,

                agent_id,

            )

            if agent_id == "package_recommender":

                artifact_payload = {

                    "recommendations": [],

                    "narrative": (

                        "We could not finish package matching right now. "

                        "Please try again in a moment."

                    ),

                }

                full_response = artifact_payload["narrative"]

                artifact_kind = "packages"

                artifacts = {"packages": artifact_payload}

            elif agent_id == "food_guide":

                full_response = "We could not finish your food guide. Please try again."

                artifact_payload = {"must_try": [], "narrative": full_response}

                artifact_kind = "food"

                artifacts = {"food": artifact_payload}

            else:

                full_response = "We could not finish your itinerary. Please try again."

                artifact_payload = {"itinerary": [], "narrative": full_response}

                artifact_kind = "itinerary"

                artifacts = {"itinerary": artifact_payload}

        finally:

            tool_events.append({"tool": tool_key, "status": "completed"})

            yield {"type": "tool_end", "tool": tool_key, "label": tool_end_label}



        thread.set_artifacts(artifacts)

        yield {
            "type": "artifact",
            "kind": artifact_kind,
            "data": artifact_payload,
        }



        journey_event = await maybe_complete_optional_agent(
            self._db, thread, user, artifact_payload
        )

        if journey_event:

            yield {"type": "journey", "data": journey_event}



        async for event in _stream_text(full_response, agent_label):

            yield event



    async def _run_concierge(

        self,

        thread: AgentThread,

        user: User,

        user_message: str,

        tool_events: list[dict[str, Any]],

    ) -> AsyncGenerator[dict[str, Any], None]:

        """Delegate to the full orchestrator via a linked concierge session."""

        ctx = dict(thread.context or {})

        session_id_str = ctx.get("session_id")

        session: Session | None = None



        if session_id_str:

            result = await self._db.execute(

                select(Session).where(Session.id == uuid.UUID(session_id_str))

            )

            session = result.scalar_one_or_none()



        if session is None or session.user_id != user.id:

            session = await create_new_session(self._db, user)

            ctx["session_id"] = str(session.id)

            thread.context = ctx

            profile = thread.get_guest_profile()

            if profile:

                session.update_guest_profile(profile)



        yield {

            "type": "tool_start",

            "tool": "orchestrator",

            "label": "Coordinating your concierge journey…",

        }

        tool_events.append({"tool": "orchestrator", "status": "started"})



        orchestrator = OrchestratorAgent(self._db)

        async for chunk in orchestrator.process_message(user_message, session):

            token = chunk.get("token", "")

            if token:

                yield {

                    "type": "token",

                    "token": token,

                    "agent": chunk.get("agent", "Concierge"),

                    "phase": chunk.get("phase"),

                }



        thread.set_guest_profile(

            {k: v for k, v in session.get_guest_profile().items() if not str(k).startswith("_last_")}

        )

        artifacts = {

            "phase": session.get_phase(),

            "session_id": str(session.id),

        }

        thread.set_artifacts(artifacts)

        tool_events.append({"tool": "orchestrator", "status": "completed"})

        yield {"type": "tool_end", "tool": "orchestrator", "label": f"Phase: {session.get_phase()}"}

        yield {"type": "artifact", "kind": "journey", "data": artifacts}


