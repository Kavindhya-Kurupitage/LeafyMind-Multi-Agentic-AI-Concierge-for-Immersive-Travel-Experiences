"""LeafyMind FastAPI application entry point."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api import agents, auth, chat, feedback, recommendations, trip_pack
from api.websocket_chat import websocket_chat_handler
from config import settings
from database import dispose_engine, init_db
from middleware.request_id import REQUEST_ID_HEADER, RequestIDMiddleware, get_request_id
from services.feedback_scheduler import feedback_scheduler
from services.knowledge_base import knowledge_base

logger = logging.getLogger(__name__)

APP_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise database schema on startup and dispose engine on shutdown."""
    await init_db()
    feedback_scheduler.start()
    kb_task = asyncio.create_task(knowledge_base.load_all())

    async def _log_kb_when_ready() -> None:
        try:
            await kb_task
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("Background knowledge base load failed: %s", exc)

    asyncio.create_task(_log_kb_when_ready())
    logger.info(
        "LeafyMind API ready (version %s) — LLM: %s; FAISS indexes loading in background",
        APP_VERSION,
        settings.llm_provider.value,
    )
    yield
    kb_task.cancel()
    try:
        await kb_task
    except asyncio.CancelledError:
        pass
    feedback_scheduler.shutdown()
    await dispose_engine()


app = FastAPI(
    title="LeafyMind API",
    description="AI concierge backend for Leafy Cave luxury cabana, Sri Lanka",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def _safe_error_response(
    request: Request,
    status_code: int,
    detail: str,
    headers: dict | None = None,
) -> JSONResponse:
    """Return a client-safe JSON error with request correlation ID."""
    response_headers = {REQUEST_ID_HEADER: get_request_id(request)}
    if headers:
        response_headers.update(headers)
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers=response_headers,
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return _safe_error_response(request, exc.status_code, detail, dict(exc.headers or {}))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    logger.info("Validation error request_id=%s", get_request_id(request))
    return _safe_error_response(request, 422, "Invalid request data")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a safe 500 response; never expose stack traces or internal paths."""
    if isinstance(exc, HTTPException):
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return _safe_error_response(request, exc.status_code, detail, dict(exc.headers or {}))

    request_id = get_request_id(request)
    logger.exception(
        "Unhandled error request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )
    return _safe_error_response(
        request,
        500,
        "An unexpected error occurred. Please try again later.",
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(trip_pack.router, prefix="/trip-pack", tags=["trip-pack"])


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str) -> None:
    """WebSocket concierge chat — authenticate via ?token= JWT query parameter."""
    await websocket_chat_handler(websocket, session_id)


@app.get("/health")
async def health_check(request: Request) -> dict:
    """Health check endpoint for Docker and load balancers."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": get_request_id(request),
    }
