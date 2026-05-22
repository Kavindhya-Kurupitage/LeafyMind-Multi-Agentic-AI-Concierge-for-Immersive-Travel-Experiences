"""WebSocket chat endpoint for real-time concierge streaming."""

import json
import logging
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from agents.orchestrator import OrchestratorAgent
from api.session_access import get_session_for_user, sanitize_message
from database import AsyncSessionLocal
from models.enums import SessionStatus
from models.user import User
from services.auth_service import verify_token

logger = logging.getLogger(__name__)


async def _load_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def websocket_chat_handler(websocket: WebSocket, session_id: str) -> None:
    """Handle WebSocket chat for a session — token via ?token= query param."""
    await websocket.accept()

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        await websocket.close(code=4002, reason="Invalid session or token")
        return

    async with AsyncSessionLocal() as db:
        payload = await verify_token(token, db)
        if not payload:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        try:
            user_uuid = uuid.UUID(payload["user_id"])
        except (KeyError, ValueError):
            await websocket.close(code=4002, reason="Invalid session or token")
            return

        user = await _load_user(db, user_uuid)
        if user is None:
            await websocket.close(code=4001, reason="Unauthorized")
            return

        try:
            session = await get_session_for_user(db, session_uuid, user)
        except Exception:
            await websocket.close(code=4003, reason="Session not found or forbidden")
            return

        if session.status != SessionStatus.ACTIVE:
            await websocket.send_json({"type": "error", "message": "Session is not active"})
            await websocket.close(code=4004, reason="Session not active")
            return

        await websocket.send_json({
            "type": "connected",
            "session_id": str(session.id),
            "phase": session.get_phase(),
        })

        orchestrator = OrchestratorAgent(db)

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    data = json.loads(raw)
                    message = data.get("message", raw)
                except json.JSONDecodeError:
                    message = raw

                message = sanitize_message(str(message))
                if not message:
                    await websocket.send_json({"type": "error", "message": "Empty message"})
                    continue

                try:
                    async for chunk in orchestrator.process_message(message, session):
                        await websocket.send_json({
                            "type": "token",
                            "token": chunk.get("token", ""),
                            "agent": chunk.get("agent", "OrchestratorAgent"),
                            "phase": chunk.get("phase", session.get_phase()),
                        })
                    await db.commit()
                    await websocket.send_json({
                        "type": "done",
                        "session_summary": {
                            "session_id": str(session.id),
                            "phase": session.get_phase(),
                            "status": session.status.value,
                        },
                    })
                except Exception as exc:
                    logger.exception("WebSocket message error: %s", exc)
                    await db.rollback()
                    await websocket.send_json({
                        "type": "error",
                        "message": "Something went wrong",
                    })

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected session=%s", session_id)
        except Exception as exc:
            logger.exception("WebSocket fatal error: %s", exc)
            await websocket.close(code=1011, reason="Internal error")
