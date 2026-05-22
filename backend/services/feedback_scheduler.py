"""Daily scheduler for post-stay feedback request emails."""

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from config import settings
from database import AsyncSessionLocal
from models.enums import SessionStatus
from models.session import Session
from services.email_service import email_service

logger = logging.getLogger(__name__)


def _parse_arrival_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()[:10]
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _stay_end_date(profile: dict[str, Any]) -> date | None:
    """Compute checkout date from arrival_date + duration_nights."""
    arrival = _parse_arrival_date(profile.get("arrival_date"))
    nights = profile.get("duration_nights")
    if arrival is None or nights is None:
        return None
    try:
        return arrival + timedelta(days=int(nights))
    except (TypeError, ValueError):
        return None


def _package_name_from_profile(profile: dict[str, Any]) -> str:
    recommendations = profile.get("_last_package_recommendations") or []
    if recommendations and isinstance(recommendations[0], dict):
        name = recommendations[0].get("name")
        if name:
            return str(name)
    selected = profile.get("selected_package")
    if selected:
        return str(selected)
    return "your Leafy Cave experience"


def _guest_display_name(profile: dict[str, Any], user_full_name: str | None) -> str:
    if user_full_name and user_full_name.strip():
        return user_full_name.strip().split()[0]
    return "Valued Guest"


class FeedbackScheduler:
    """
    Runs daily at 9:00 AM Sri Lanka time (Asia/Colombo).
    Sends feedback emails for stays that ended on the target date
    (today minus FEEDBACK_EMAIL_DELAY_DAYS).
    """

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="Asia/Colombo")

    def start(self) -> None:
        if not email_service.is_configured:
            logger.info(
                "Feedback email scheduler disabled — set GMAIL_SENDER_ADDRESS and "
                "GMAIL_APP_PASSWORD to enable daily post-stay emails"
            )
            return

        self.scheduler.add_job(
            self._check_and_send_feedback_emails,
            CronTrigger(hour=9, minute=0, timezone="Asia/Colombo"),
            id="daily_feedback_emails",
            replace_existing=True,
        )
        self.scheduler.start()
        logger.info(
            "Feedback email scheduler started — runs daily at 9:00 AM (Sri Lanka time)"
        )

    async def _check_and_send_feedback_emails(self) -> None:
        """Find completed stays that ended on the target date and send feedback emails."""
        delay = max(0, int(settings.feedback_email_delay_days))
        target_end_date = date.today() - timedelta(days=delay)
        logger.info(
            "Feedback email job: checking stays that ended on %s (delay_days=%s)",
            target_end_date,
            delay,
        )

        sent_count = 0
        skipped_no_email = 0

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Session)
                .options(selectinload(Session.user))
                .where(
                    Session.status == SessionStatus.COMPLETED,
                    Session.feedback_email_sent.is_(False),
                )
            )
            sessions = list(result.scalars().all())

            for session in sessions:
                profile = session.get_guest_profile()
                stay_end = _stay_end_date(profile)
                if stay_end != target_end_date:
                    continue

                guest_email = (profile.get("email") or "").strip()
                if not guest_email:
                    skipped_no_email += 1
                    continue

                guest_name = _guest_display_name(
                    profile,
                    session.user.full_name if session.user else None,
                )
                stay_summary = {
                    "package_name": _package_name_from_profile(profile),
                    "duration_nights": profile.get("duration_nights", 2),
                }

                sent = await email_service.send_feedback_request(
                    guest_email,
                    guest_name,
                    str(session.id),
                    stay_summary,
                )
                if sent:
                    session.feedback_email_sent = True
                    session.feedback_email_sent_at = datetime.now(timezone.utc)
                    sent_count += 1

            if sent_count:
                await db.commit()
                logger.info("Feedback emails sent: %s", sent_count)
            if skipped_no_email:
                logger.info("Sessions skipped (no guest email in profile): %s", skipped_no_email)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Feedback email scheduler stopped")


feedback_scheduler = FeedbackScheduler()
