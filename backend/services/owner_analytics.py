"""Owner dashboard analytics queries."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import SessionStatus
from models.feedback import Feedback
from models.session import Session


def _feedback_to_dict(f: Feedback) -> dict[str, Any]:
    return {
        "id": str(f.id),
        "session_id": str(f.session_id),
        "user_id": str(f.user_id),
        "package_rating": f.package_rating,
        "food_rating": f.food_rating,
        "itinerary_rating": f.itinerary_rating,
        "ai_helpfulness_rating": f.ai_helpfulness_rating,
        "free_text_feedback": f.free_text_feedback,
        "auto_tags": f.auto_tags or [],
        "flagged_for_review": f.flagged_for_review,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


async def get_owner_dashboard_summary(db: AsyncSession) -> dict[str, Any]:
    """Build aggregated metrics for the owner dashboard."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)

    sessions_week_result = await db.execute(
        select(func.count(Session.id)).where(Session.created_at >= week_ago)
    )
    total_sessions_week = sessions_week_result.scalar() or 0

    active_result = await db.execute(
        select(func.count(Session.id)).where(Session.status == SessionStatus.ACTIVE)
    )
    active_sessions = active_result.scalar() or 0

    flagged_result = await db.execute(
        select(func.count(Feedback.id)).where(Feedback.flagged_for_review.is_(True))
    )
    flagged_count = flagged_result.scalar() or 0

    avg_result = await db.execute(
        select(
            func.avg(Feedback.package_rating),
            func.avg(Feedback.food_rating),
            func.avg(Feedback.itinerary_rating),
            func.avg(Feedback.ai_helpfulness_rating),
        )
    )
    avgs = avg_result.one()

    recent_result = await db.execute(
        select(Feedback).order_by(Feedback.created_at.desc()).limit(20)
    )
    recent_feedback = recent_result.scalars().all()

    sessions_result = await db.execute(
        select(Session).where(Session.created_at >= week_ago)
    )
    package_counter: Counter[str] = Counter()
    for session in sessions_result.scalars().all():
        profile = session.get_guest_profile()
        for rec in profile.get("_last_package_recommendations") or []:
            if isinstance(rec, dict):
                name = rec.get("name")
                if name:
                    package_counter[name] += 1

    most_recommended_package = None
    if package_counter:
        most_recommended_package = package_counter.most_common(1)[0][0]

    return {
        "total_sessions_week": total_sessions_week,
        "active_sessions": active_sessions,
        "flagged_count": flagged_count,
        "most_recommended_package": most_recommended_package,
        "avg_ratings": {
            "package": round(float(avgs[0] or 0), 2),
            "food": round(float(avgs[1] or 0), 2),
            "itinerary": round(float(avgs[2] or 0), 2),
            "ai": round(float(avgs[3] or 0), 2),
        },
        "recent_feedback": [_feedback_to_dict(f) for f in recent_feedback],
    }
