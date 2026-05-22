"""Guest journey state for the Agent Hub dashboard (profile → planning → feedback)."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.profile_builder import ProfileBuilderAgent
from models.agent_message import AgentMessage
from models.agent_thread import AgentThread
from models.enums import AgentThreadStatus, SessionStatus
from models.session import Session
from services.guest_profile_seed import seed_guest_profile

HubAgentId = Literal[
    "profile_builder",
    "package_recommender",
    "food_guide",
    "itinerary_planner",
    "feedback_collector",
]

HUB_AGENT_IDS: tuple[str, ...] = (
    "profile_builder",
    "package_recommender",
    "food_guide",
    "itinerary_planner",
    "feedback_collector",
)

OPTIONAL_AGENT_IDS: tuple[str, ...] = (
    "package_recommender",
    "food_guide",
    "itinerary_planner",
)

StepStatus = Literal["locked", "available", "in_progress", "completed"]



def _planning_block(agent_id: str, artifacts: dict[str, Any]) -> dict[str, Any]:
    """Return the specialist payload (supports nested or legacy flat artifacts)."""
    if agent_id == "food_guide":
        return artifacts.get("food") or artifacts
    if agent_id == "package_recommender":
        return artifacts.get("packages") or artifacts
    if agent_id == "itinerary_planner":
        block = artifacts.get("itinerary")
        if isinstance(block, dict):
            return block
        if isinstance(block, list):
            return {"itinerary": block}
        return artifacts
    return artifacts


def _optional_artifacts_complete(agent_id: str, artifacts: dict[str, Any]) -> bool:
    """True when the specialist produced usable structured output."""
    block = _planning_block(agent_id, artifacts)
    if agent_id == "package_recommender":
        return bool(block.get("recommendations"))
    if agent_id == "food_guide":
        return bool(block.get("must_try"))
    if agent_id == "itinerary_planner":
        days = block.get("itinerary") or []
        return bool(days)
    return False


def _profile_from_threads(threads: list[AgentThread], seeded: dict[str, Any]) -> dict[str, Any]:
    """Merge the richest guest profile from threads and seed data."""
    profile = dict(seeded)
    for thread in threads:
        if thread.agent_id == "profile_builder":
            pb = thread.get_guest_profile()
            if pb:
                profile.update({k: v for k, v in pb.items() if not str(k).startswith("_")})
    for thread in sorted(threads, key=lambda t: t.updated_at or t.created_at, reverse=True):
        gp = thread.get_guest_profile()
        if gp:
            for k, v in gp.items():
                if not str(k).startswith("_") and v is not None and v != "":
                    profile.setdefault(k, v)
    return profile


def _thread_step_status(
    thread: AgentThread | None,
    agent_id: str,
    message_count: int = 0,
) -> StepStatus:
    if thread is None:
        return "available"
    artifacts = thread.get_artifacts()
    if thread.status == AgentThreadStatus.COMPLETED:
        return "completed"
    if agent_id == "profile_builder":
        if artifacts.get("is_complete"):
            return "completed"
    elif agent_id in OPTIONAL_AGENT_IDS:
        if _optional_artifacts_complete(agent_id, artifacts):
            return "completed"
    elif agent_id == "feedback_collector":
        if artifacts.get("survey_complete"):
            return "completed"
    if message_count > 0:
        return "in_progress"
    return "available"


class JourneyService:
    """Computes hub dashboard progress and access rules per user."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_journey(self, user_id: uuid.UUID) -> dict[str, Any]:
        seeded = await seed_guest_profile(self._db, user_id)
        result = await self._db.execute(
            select(AgentThread)
            .where(
                AgentThread.user_id == user_id,
                AgentThread.agent_id.in_(HUB_AGENT_IDS),
            )
            .order_by(AgentThread.updated_at.desc())
        )
        threads = list(result.scalars().all())
        threads_by_agent: dict[str, AgentThread] = {}
        for thread in threads:
            if thread.agent_id not in threads_by_agent:
                threads_by_agent[thread.agent_id] = thread

        message_counts: dict[uuid.UUID, int] = {}
        thread_ids = [t.id for t in threads]
        if thread_ids:
            count_rows = await self._db.execute(
                select(AgentMessage.thread_id, func.count(AgentMessage.id))
                .where(AgentMessage.thread_id.in_(thread_ids))
                .group_by(AgentMessage.thread_id)
            )
            message_counts = {row[0]: int(row[1]) for row in count_rows.all()}

        profile = _profile_from_threads(threads, seeded)
        profile_complete = ProfileBuilderAgent.is_profile_complete(profile)

        optional_completed: list[str] = []
        for agent_id in OPTIONAL_AGENT_IDS:
            thread = threads_by_agent.get(agent_id)
            if thread and (
                thread.status == AgentThreadStatus.COMPLETED
                or _optional_artifacts_complete(agent_id, thread.get_artifacts())
            ):
                optional_completed.append(agent_id)

        feedback_thread = threads_by_agent.get("feedback_collector")
        feedback_survey_done = bool(
            feedback_thread and feedback_thread.get_artifacts().get("survey_complete")
        )

        session_result = await self._db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.updated_at.desc())
            .limit(1)
        )
        latest_session = session_result.scalar_one_or_none()
        feedback_email_sent = bool(
            latest_session and latest_session.feedback_email_sent
        )
        feedback_session_id = (
            str(latest_session.id) if latest_session else None
        )

        feedback_unlocked = profile_complete and (
            len(optional_completed) > 0 or feedback_email_sent
        )

        steps: dict[str, dict[str, Any]] = {}
        for agent_id in HUB_AGENT_IDS:
            thread = threads_by_agent.get(agent_id)
            raw_status = _thread_step_status(
                thread,
                agent_id,
                message_counts.get(thread.id, 0) if thread else 0,
            )

            if agent_id == "profile_builder":
                status: StepStatus = "completed" if profile_complete else raw_status
                locked = False
                required = True
            elif agent_id in OPTIONAL_AGENT_IDS:
                locked = not profile_complete
                required = False
                if locked:
                    status = "locked"
                elif raw_status == "available" and agent_id in optional_completed:
                    status = "completed"
                else:
                    status = raw_status
            else:
                required = False
                locked = not feedback_unlocked
                if locked:
                    status = "locked"
                elif feedback_survey_done:
                    status = "completed"
                elif feedback_email_sent or raw_status != "available":
                    status = raw_status if raw_status != "locked" else "available"
                else:
                    status = "available"

            steps[agent_id] = {
                "status": status,
                "locked": locked,
                "required": required,
                "thread_id": str(thread.id) if thread else None,
            }

        current_step = self._resolve_current_step(steps, profile_complete, optional_completed)

        return {
            "profile_complete": profile_complete,
            "profile_completeness": self._completeness(profile),
            "optional_agents_completed": optional_completed,
            "feedback_unlocked": feedback_unlocked,
            "feedback_email_sent": feedback_email_sent,
            "feedback_survey_complete": feedback_survey_done,
            "feedback_session_id": feedback_session_id,
            "current_step": current_step,
            "steps": steps,
        }

    @staticmethod
    def _completeness(profile: dict[str, Any]) -> int:
        if ProfileBuilderAgent.is_profile_complete(profile):
            return 100
        model_fields = [
            profile.get("travel_style"),
            profile.get("group_type"),
            profile.get("budget_tier"),
            profile.get("dietary_restrictions") is not None,
            profile.get("duration_nights"),
        ]
        filled = sum(1 for item in model_fields if item)
        return int((filled / len(model_fields)) * 100) if model_fields else 0

    @staticmethod
    def _resolve_current_step(
        steps: dict[str, dict[str, Any]],
        profile_complete: bool,
        optional_completed: list[str],
    ) -> str:
        if not profile_complete:
            return "profile_builder"
        if not optional_completed:
            return "package_recommender"
        fb = steps.get("feedback_collector", {})
        if fb.get("status") != "completed" and fb.get("status") != "locked":
            return "feedback_collector"
        return optional_completed[-1]

    def can_open_agent(self, journey: dict[str, Any], agent_id: str) -> str | None:
        """Return an error message if the agent is locked, else None."""
        step = journey.get("steps", {}).get(agent_id)
        if not step:
            return "Unknown agent"
        if step.get("locked"):
            if agent_id == "profile_builder":
                return None
            if agent_id == "feedback_collector":
                return (
                    "Complete your travel profile and use at least one planning agent "
                    "(packages, food, or itinerary) before sharing feedback."
                )
            return "Complete your travel profile with the Profile Builder first."
        return None


async def get_user_journey(db: AsyncSession, user_id: uuid.UUID) -> dict[str, Any]:
    """Shortcut for journey snapshot."""
    return await JourneyService(db).get_journey(user_id)
