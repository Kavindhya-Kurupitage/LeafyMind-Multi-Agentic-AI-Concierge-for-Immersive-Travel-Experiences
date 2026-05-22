"""
Manually run the daily feedback email job (for testing).

Usage (from backend/):
    python scripts/send_feedback_emails_now.py

Set FEEDBACK_EMAIL_DELAY_DAYS=0 in .env so stays ending today qualify.
"""

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(BACKEND_ROOT.parent / ".env")

import models  # noqa: E402, F401
from database import init_db  # noqa: E402
from services.feedback_scheduler import feedback_scheduler  # noqa: E402


async def main() -> None:
    await init_db()
    await feedback_scheduler._check_and_send_feedback_emails()
    print("Feedback email job finished.")


if __name__ == "__main__":
    asyncio.run(main())
