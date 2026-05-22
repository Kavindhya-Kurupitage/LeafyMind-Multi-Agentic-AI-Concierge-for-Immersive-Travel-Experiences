"""Trip pack API — aggregated plan preview, PDF download, and email delivery."""

from __future__ import annotations

import logging
import re
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from database import get_db
from models.user import User
from services.email_service import email_service
from services.trip_pdf_service import trip_pdf_service
from services.trip_summary_service import TripSummaryService

logger = logging.getLogger(__name__)

router = APIRouter()


class TripPackEmailRequest(BaseModel):
    email: EmailStr | None = Field(
        None,
        description="Override recipient; defaults to email on travel profile",
    )


class TripPackEmailResponse(BaseModel):
    sent: bool
    message: str


def _safe_pdf_filename(guest_name: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", guest_name or "Guest").strip().replace(" ", "-")
    slug = slug[:40] or "Guest"
    return f"Leafy-Cave-Trip-Plan-{slug}.pdf"


@router.get("/summary")
async def get_trip_pack_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict[str, Any]:
    """Return aggregated trip pack for hub preview (packages, food, itinerary)."""
    return await TripSummaryService(db).build_summary(user.id)


@router.get("/pdf")
async def download_trip_pack_pdf(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    """Download branded PDF trip plan (requires all three planners complete)."""
    svc = TripSummaryService(db)
    summary = await svc.build_summary(user.id)
    if not summary.get("trip_pack_ready"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete Package, Food, and Itinerary agents before downloading your trip pack.",
        )
    try:
        pdf_bytes = trip_pdf_service.generate_pdf(summary)
    except RuntimeError as exc:
        logger.exception("PDF generation failed for user %s", user.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    filename = _safe_pdf_filename(summary.get("guest_name") or "Guest")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/email", response_model=TripPackEmailResponse)
async def email_trip_pack(
    body: TripPackEmailRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TripPackEmailResponse:
    """Email the trip plan PDF to the guest (on-demand; requires trip pack ready)."""
    svc = TripSummaryService(db)
    summary = await svc.build_summary(user.id)

    if not summary.get("trip_pack_ready"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete Package, Food, and Itinerary agents before emailing your trip pack.",
        )

    recipient = (body.email or summary.get("guest_email") or "").strip()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add your email in Profile Builder, or provide an email address.",
        )

    if not email_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email is not configured on this server. Contact your host to enable Gmail SMTP.",
        )

    try:
        pdf_bytes = trip_pdf_service.generate_pdf(summary)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    guest_name = summary.get("guest_name") or "Guest"
    filename = _safe_pdf_filename(guest_name)
    sent = await email_service.send_trip_plan_email(
        guest_email=recipient,
        guest_name=guest_name,
        pdf_bytes=pdf_bytes,
        pdf_filename=filename,
    )

    if not sent:
        return TripPackEmailResponse(
            sent=False,
            message="We could not send the email. Check the address and try again later.",
        )

    profile = summary.get("profile") or {}
    await svc.mark_email_sent(user, profile)
    await db.commit()

    return TripPackEmailResponse(
        sent=True,
        message=f"Your Leafy Cave trip plan was sent to {recipient}.",
    )
