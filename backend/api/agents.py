"""Agent Hub API — per-agent threads, streaming messages, and dashboard metadata."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.registry import get_agent, list_agents
from api.deps import get_current_user
from api.session_access import sanitize_message
from database import get_db
from models.agent_message import AgentMessage
from models.agent_thread import AgentThread
from models.enums import AgentThreadStatus
from models.user import User
from agents.guided_steps import GUIDED_AGENTS
from services.agent_runner import AgentRunner
from services.guided_flow import GuidedFlowService
from services.guest_profile_seed import seed_guest_profile
from services.journey_service import HUB_AGENT_IDS, JourneyService
from services.trip_summary_service import TripSummaryService
from services.specialist_interview import OPTIONAL_PLANNING_AGENTS, SpecialistInterviewService

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentInfoResponse(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    icon: str
    color: str
    capabilities: list[str]
    artifact_kind: str | None


class ThreadCreateRequest(BaseModel):
    title: str | None = Field(None, max_length=255)
    feedback_session_id: str | None = Field(None, description="Link hub feedback to a concierge session")


class ThreadSummaryResponse(BaseModel):
    id: str
    agent_id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ThreadDetailResponse(BaseModel):
    id: str
    agent_id: str
    title: str
    status: str
    created_at: datetime | None
    updated_at: datetime | None
    guest_profile: dict[str, Any]
    artifacts: dict[str, Any]
    agent_preferences: dict[str, Any] = Field(default_factory=dict)
    interview_phase: str | None = None
    guided_turn: dict[str, Any] | None = None
    messages: list[dict[str, Any]]


class GuidedResponseBody(BaseModel):
    step_id: str = Field(..., min_length=1, max_length=64)
    selected: list[str] = Field(default_factory=list)
    free_text: str | None = Field(None, max_length=2000)


class AgentMessageRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    guided_response: GuidedResponseBody | None = None


class JourneyStepResponse(BaseModel):
    status: str
    locked: bool
    required: bool
    thread_id: str | None = None


class JourneyResponse(BaseModel):
    profile_complete: bool
    profile_completeness: int
    optional_agents_completed: list[str]
    feedback_unlocked: bool
    feedback_email_sent: bool
    feedback_survey_complete: bool
    feedback_session_id: str | None
    trip_pack_ready: bool = False
    trip_pack_email_sent: bool = False
    trip_pack_planners_done: dict[str, bool] = Field(default_factory=dict)
    current_step: str
    steps: dict[str, JourneyStepResponse]


def _format_sse(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload)}\n\n"


def _agent_to_response(agent_def: Any) -> AgentInfoResponse:
    return AgentInfoResponse(
        id=agent_def.id,
        name=agent_def.name,
        tagline=agent_def.tagline,
        description=agent_def.description,
        icon=agent_def.icon,
        color=agent_def.color,
        capabilities=list(agent_def.capabilities),
        artifact_kind=agent_def.artifact_kind,
    )


async def _get_thread_for_user(
    db: AsyncSession,
    thread_id: uuid.UUID,
    user: User,
) -> AgentThread:
    result = await db.execute(
        select(AgentThread)
        .where(AgentThread.id == thread_id)
        .options(selectinload(AgentThread.messages))
    )
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
    if thread.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return thread


@router.get("", response_model=list[AgentInfoResponse])
async def list_available_agents() -> list[AgentInfoResponse]:
    """Return all specialist agents for the guest hub dashboard."""
    return [_agent_to_response(agent) for agent in list_agents()]


@router.get("/journey", response_model=JourneyResponse)
async def get_guest_journey(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> JourneyResponse:
    """Return guided journey progress for the hub dashboard."""
    journey = await JourneyService(db).get_journey(user.id)
    trip_summary = await TripSummaryService(db).build_summary(user.id)
    steps = {
        agent_id: JourneyStepResponse(**step)
        for agent_id, step in journey["steps"].items()
    }
    return JourneyResponse(
        profile_complete=journey["profile_complete"],
        profile_completeness=journey["profile_completeness"],
        optional_agents_completed=journey["optional_agents_completed"],
        feedback_unlocked=journey["feedback_unlocked"],
        feedback_email_sent=journey["feedback_email_sent"],
        feedback_survey_complete=journey["feedback_survey_complete"],
        feedback_session_id=journey["feedback_session_id"],
        trip_pack_ready=trip_summary.get("trip_pack_ready", False),
        trip_pack_email_sent=trip_summary.get("trip_pack_email_sent", False),
        trip_pack_planners_done=trip_summary.get("planners_done") or {},
        current_step=journey["current_step"],
        steps=steps,
    )


@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread_detail(
    thread_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ThreadDetailResponse:
    """Return thread history, profile context, and artifacts."""
    thread = await _get_thread_for_user(db, thread_id, user)
    messages = sorted(thread.messages or [], key=lambda m: m.created_at or datetime.min)
    return ThreadDetailResponse(
        id=str(thread.id),
        agent_id=thread.agent_id,
        title=thread.title,
        status=thread.status.value,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        guest_profile=thread.get_guest_profile(),
        artifacts=thread.get_artifacts(),
        agent_preferences=thread.get_agent_preferences(),
        interview_phase=thread.get_interview_phase(),
        guided_turn=(thread.context or {}).get("last_guided_turn"),
        messages=[
            {
                "id": str(msg.id),
                "role": msg.role,
                "content": msg.content,
                "agent_id": msg.agent_id,
                "tool_events": msg.tool_events,
                "artifacts": msg.artifacts,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    )


@router.post("/threads/{thread_id}/message")
async def post_thread_message(
    thread_id: uuid.UUID,
    body: AgentMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Stream an agent reply via Server-Sent Events."""
    thread = await _get_thread_for_user(db, thread_id, user)

    if thread.agent_id in HUB_AGENT_IDS:
        journey = await JourneyService(db).get_journey(user.id)
        lock_reason = JourneyService(db).can_open_agent(journey, thread.agent_id)
        if lock_reason:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=lock_reason)

    if thread.status != AgentThreadStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Thread is not active",
        )

    guided = body.guided_response
    message = sanitize_message(body.message) if body.message else ""
    if guided is None and not message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide a guided selection or message",
        )
    if guided is None:
        message = message or "continue"

    async def event_stream() -> AsyncGenerator[str, None]:
        runner = AgentRunner(db)
        try:
            async for event in runner.process_message(
                thread,
                user,
                message,
                guided_response=guided.model_dump() if guided else None,
            ):
                yield _format_sse(event)
            await db.flush()
        except Exception as exc:
            logger.exception("Agent stream error thread=%s: %s", thread_id, exc)
            await db.rollback()
            yield _format_sse({"type": "error", "message": "Something went wrong"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{agent_id}", response_model=AgentInfoResponse)
async def get_agent_info(agent_id: str) -> AgentInfoResponse:
    """Return metadata for a single agent."""
    agent_def = get_agent(agent_id)
    if agent_def is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return _agent_to_response(agent_def)


@router.post("/{agent_id}/threads", response_model=ThreadSummaryResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    agent_id: str,
    body: ThreadCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ThreadSummaryResponse:
    """Start a new conversation thread for the given agent."""
    agent_def = get_agent(agent_id)
    if agent_def is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    journey_svc = JourneyService(db)
    journey: dict[str, Any] | None = None
    if agent_id in HUB_AGENT_IDS:
        journey = await journey_svc.get_journey(user.id)
        lock_reason = journey_svc.can_open_agent(journey, agent_id)
        if lock_reason:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=lock_reason)

    profile = await seed_guest_profile(db, user.id)
    thread_context: dict[str, Any] = {
        "guest_profile": profile,
        "artifacts": {},
        "guided_step_index": 0,
        "interview_phase": "discovery",
    }
    message_count = 0

    if agent_id in OPTIONAL_PLANNING_AGENTS:
        prefs = SpecialistInterviewService.seed_preferences(agent_id, profile)
        thread_context["agent_preferences"] = prefs

    if agent_id == "feedback_collector":
        session_link = body.feedback_session_id or (
            journey.get("feedback_session_id") if journey else None
        )
        if session_link:
            thread_context["feedback_session_id"] = session_link

    thread = AgentThread(
        user_id=user.id,
        agent_id=agent_id,
        title=body.title or "New conversation",
        status=AgentThreadStatus.ACTIVE,
        context=thread_context,
    )
    db.add(thread)
    await db.flush()

    if agent_id in GUIDED_AGENTS:
        flow = GuidedFlowService()
        initial = flow.get_initial_turn(thread)
        ctx = dict(thread_context)
        if initial.guided_turn:
            ctx["last_guided_turn"] = initial.guided_turn
        thread.context = ctx
        welcome = AgentMessage(
            thread_id=thread.id,
            role="assistant",
            content=initial.assistant_content,
            agent_id=agent_id,
            artifacts={"guided_turn": initial.guided_turn} if initial.guided_turn else {},
        )
        db.add(welcome)
        await db.flush()
        message_count = 1
    else:
        message_count = 0

    await db.refresh(thread)

    return ThreadSummaryResponse(
        id=str(thread.id),
        agent_id=thread.agent_id,
        title=thread.title,
        status=thread.status.value,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        message_count=message_count,
    )


@router.get("/{agent_id}/threads", response_model=list[ThreadSummaryResponse])
async def list_threads(
    agent_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[ThreadSummaryResponse]:
    """List the user's threads for one agent."""
    if get_agent(agent_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    threads = await AgentThread.list_for_user(db, user.id, agent_id=agent_id)
    summaries: list[ThreadSummaryResponse] = []
    for thread in threads:
        count_result = await db.execute(
            select(AgentMessage.id).where(AgentMessage.thread_id == thread.id)
        )
        message_count = len(count_result.all())
        summaries.append(
            ThreadSummaryResponse(
                id=str(thread.id),
                agent_id=thread.agent_id,
                title=thread.title,
                status=thread.status.value,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                message_count=message_count,
            )
        )
    return summaries
