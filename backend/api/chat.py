"""Chat API — sessions, streaming messages, and conversation history."""

import json
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrator import OrchestratorAgent
from api.deps import get_current_user
from api.session_access import (
    create_new_session,
    get_session_for_user,
    sanitize_message,
)
from database import get_db
from models.enums import SessionStatus
from models.session import Session
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()
HISTORY_PAGE_SIZE = 20


class SessionStartResponse(BaseModel):
    session_id: str
    created_at: datetime
    status: str


class ChatMessageRequest(BaseModel):
    session_id: uuid.UUID
    message: str = Field(..., min_length=1, max_length=2000)


class SessionEndResponse(BaseModel):
    message: str
    redirect_to_feedback: bool = True


def _format_sse(payload: dict[str, Any]) -> str:
    """Format a dict as a Server-Sent Events data line."""
    return f"data: {json.dumps(payload)}\n\n"


def _session_summary(session: Session) -> dict[str, Any]:
    """Build a summary payload for stream completion events."""
    profile = session.get_guest_profile()
    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "phase": session.get_phase(),
        "guest_profile": {
            k: v for k, v in profile.items() if not str(k).startswith("_last_")
        },
        "message_count": len(session.get_conversation_history()),
    }


def _paginate_history(
    history: list[dict[str, Any]],
    page: int,
    page_size: int = HISTORY_PAGE_SIZE,
) -> dict[str, Any]:
    """Return a page of conversation history (1-indexed)."""
    page = max(1, page)
    start = (page - 1) * page_size
    end = start + page_size
    items = history[start:end]
    total = len(history)
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "messages": items,
    }


@router.post("/session/start", response_model=SessionStartResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SessionStartResponse:
    """Create a new concierge session for the authenticated guest."""
    session = await create_new_session(db, user)
    return SessionStartResponse(
        session_id=str(session.id),
        created_at=session.created_at,
        status=session.status.value,
    )


@router.get("/session/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return full session details including history and guest profile."""
    session = await get_session_for_user(db, session_id, user)
    profile = session.get_guest_profile()
    return {
        "session_id": str(session.id),
        "status": session.status.value,
        "phase": session.get_phase(),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "conversation_history": session.get_conversation_history(),
        "guest_profile": {k: v for k, v in profile.items() if not str(k).startswith("_last_")},
    }


@router.post("/message")
async def post_message(
    body: ChatMessageRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> StreamingResponse:
    """Stream an orchestrated concierge reply via Server-Sent Events."""
    session = await get_session_for_user(db, body.session_id, user)

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    message = sanitize_message(body.message)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message cannot be empty after sanitisation",
        )

    async def event_stream() -> AsyncGenerator[str, None]:
        orchestrator = OrchestratorAgent(db)
        try:
            async for chunk in orchestrator.process_message(message, session):
                yield _format_sse({
                    "token": chunk.get("token", ""),
                    "agent": chunk.get("agent", "OrchestratorAgent"),
                    "phase": chunk.get("phase", session.get_phase()),
                })
            await db.flush()
            yield _format_sse({
                "type": "done",
                "session_summary": _session_summary(session),
            })
        except Exception as exc:
            logger.exception("Chat stream error session=%s: %s", session.id, exc)
            await db.rollback()
            yield _format_sse({
                "type": "error",
                "message": "Something went wrong",
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{session_id}")
async def get_history(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
) -> dict[str, Any]:
    """Return paginated conversation history for a session."""
    session = await get_session_for_user(db, session_id, user)
    return _paginate_history(session.get_conversation_history(), page)


@router.post("/session/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SessionEndResponse:
    """Mark session completed and transition to feedback phase."""
    session = await get_session_for_user(db, session_id, user)
    session.status = SessionStatus.COMPLETED
    session.set_phase("FEEDBACK")
    await db.flush()
    return SessionEndResponse(
        message=(
            "Thank you for chatting with LeafyMind! We'd love to hear how we did — "
            "your feedback helps us welcome future guests even better."
        ),
        redirect_to_feedback=True,
    )
