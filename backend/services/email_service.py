"""
Gmail SMTP email delivery for post-stay feedback requests.

Gmail SMTP setup (free — no third-party email service required):
  1. Create or use a Gmail account (e.g. leafycave.noreply@gmail.com).
  2. Enable 2-Factor Authentication on that Google account.
  3. Google Account → Security → App Passwords.
  4. Generate an App Password for "Mail" (16-character code).
  5. Set GMAIL_APP_PASSWORD in .env to that code — NOT your normal Gmail password.
  6. SMTP: host=smtp.gmail.com, port=587, STARTTLS=True.
"""

import asyncio
import logging
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Send branded Leafy Cave transactional email via Gmail SMTP."""

    def __init__(self) -> None:
        self.sender = settings.gmail_sender_address.strip()
        self.password = settings.gmail_app_password.strip()
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 587

    @property
    def is_configured(self) -> bool:
        return bool(self.sender and self.password)

    async def send_feedback_request(
        self,
        guest_email: str,
        guest_name: str,
        session_id: str,
        stay_summary: dict[str, Any],
        *,
        feedback_path: str | None = None,
    ) -> bool:
        """
        Send a warm post-stay feedback request email.
        Returns True if sent successfully, False if failed.
        Never raises exceptions — log and return False on any error.
        """
        if not self.is_configured:
            logger.warning("Gmail SMTP not configured; skipping feedback email to %s", guest_email)
            return False

        if not guest_email or "@" not in guest_email:
            logger.warning("Invalid guest email for feedback request: %r", guest_email)
            return False

        try:
            html_body = self._build_feedback_email_html(
                guest_name, session_id, stay_summary, feedback_path=feedback_path
            )
            plain_body = self._build_feedback_email_plain(
                guest_name, session_id, stay_summary, feedback_path=feedback_path
            )

            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"Quick planning survey (trip PDF is separate), {guest_name}"
            )
            msg["From"] = f"Leafy Cave Concierge <{self.sender}>"
            msg["To"] = guest_email

            msg.attach(MIMEText(plain_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, guest_email)
            logger.info("Feedback email sent to %s for session %s", guest_email, session_id)
            return True
        except Exception as exc:
            logger.error("Failed to send feedback email to %s: %s", guest_email, exc)
            return False

    async def send_trip_plan_email(
        self,
        guest_email: str,
        guest_name: str,
        pdf_bytes: bytes,
        *,
        pdf_filename: str = "Leafy-Cave-Trip-Plan.pdf",
    ) -> bool:
        """
        Send branded trip plan email with PDF attachment.
        Returns True if sent successfully; never raises.
        """
        if not self.is_configured:
            logger.warning("Gmail SMTP not configured; skipping trip plan email to %s", guest_email)
            return False

        if not guest_email or "@" not in guest_email:
            logger.warning("Invalid guest email for trip plan: %r", guest_email)
            return False

        if not pdf_bytes:
            logger.warning("Empty PDF for trip plan email to %s", guest_email)
            return False

        try:
            html_body = self._build_trip_plan_email_html(guest_name)
            plain_body = self._build_trip_plan_email_plain(guest_name)

            msg = MIMEMultipart("mixed")
            msg["Subject"] = f"Your Leafy Cave trip plan, {guest_name} 🌿"
            msg["From"] = f"Leafy Cave Concierge <{self.sender}>"
            msg["To"] = guest_email

            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(plain_body, "plain", "utf-8"))
            alt.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(alt)

            attachment = MIMEApplication(pdf_bytes, _subtype="pdf")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=pdf_filename,
            )
            msg.attach(attachment)

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._send_smtp, msg, guest_email)
            logger.info("Trip plan email sent to %s", guest_email)
            return True
        except Exception as exc:
            logger.error("Failed to send trip plan email to %s: %s", guest_email, exc)
            return False

    def _build_trip_plan_email_html(self, name: str) -> str:
        hub_url = f"{settings.frontend_url.rstrip('/')}/agents"
        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Georgia, serif; background: #f5f0e8; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 0 auto; background: white; }}
    .header {{ background: #1a4731; padding: 36px; text-align: center; }}
    .header h1 {{ color: #c9a84c; font-size: 26px; margin: 0; letter-spacing: 2px; }}
    .header p {{ color: #f5f0e8; margin: 8px 0 0; font-size: 14px; }}
    .body {{ padding: 36px; color: #333; line-height: 1.8; }}
    .body h2 {{ color: #1a4731; }}
    .highlight {{
      background: #faf8f4; border-left: 4px solid #c9a84c;
      padding: 16px 20px; margin: 20px 0; border-radius: 0 4px 4px 0;
    }}
    .footer {{ background: #1a4731; padding: 20px; text-align: center;
               color: #f5f0e8; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🌿 LEAFY CAVE</h1>
      <p>Wellawaya, Sri Lanka</p>
    </div>
    <div class="body">
      <h2>Dear {name},</h2>
      <p>
        Your personalised LeafyMind trip plan is ready — attached as a PDF with your
        cabana package picks, Sri Lankan food guide (with photos), and day-by-day itinerary.
      </p>
      <div class="highlight">
        <strong>What's inside:</strong>
        <ul>
          <li>Travel profile summary</li>
          <li>Recommended Leafy Cave packages</li>
          <li>Must-try dishes with images</li>
          <li>Your curated itinerary</li>
        </ul>
      </div>
      <p>
        Open the attachment on your phone or laptop before you travel. You can also
        revisit your plan anytime in the
        <a href="{hub_url}" style="color:#1a4731;">LeafyMind Agent Hub</a>.
      </p>
      <p>
        With warmth,<br>
        <strong>Pramitha Madushanka</strong><br>
        <em>Owner, Leafy Cave Cabana</em>
      </p>
    </div>
    <div class="footer">
      Leafy Cave Luxury Cabana · Wellawaya, Sri Lanka<br>
      You received this because you requested your trip plan from LeafyMind.
    </div>
  </div>
</body>
</html>"""

    def _build_trip_plan_email_plain(self, name: str) -> str:
        hub_url = f"{settings.frontend_url.rstrip('/')}/agents"
        return f"""Dear {name},

Your personalised Leafy Cave trip plan is attached as a PDF.

It includes your travel profile, recommended cabana packages, Sri Lankan food guide with photos, and your day-by-day itinerary.

You can also view your plan online: {hub_url}

With warmth,
Pramitha Madushanka
Owner, Leafy Cave Cabana
"""

    def _send_smtp(self, msg: MIMEMultipart, recipient: str) -> None:
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.sender, self.password)
            server.sendmail(self.sender, [recipient], msg.as_string())

    def _feedback_url(self, session_id: str, feedback_path: str | None = None) -> str:
        base = settings.frontend_url.rstrip("/")
        if feedback_path:
            path = feedback_path if feedback_path.startswith("/") else f"/{feedback_path}"
            return f"{base}{path}"
        return f"{base}/agents/feedback_collector?session={session_id}"

    def _build_feedback_email_html(
        self,
        name: str,
        session_id: str,
        summary: dict[str, Any],
        *,
        feedback_path: str | None = None,
    ) -> str:
        feedback_url = self._feedback_url(session_id, feedback_path)
        package_name = summary.get("package_name", "your Leafy Cave experience")
        nights = summary.get("duration_nights", "your")
        is_planning = feedback_path and "/agents/" in feedback_path
        intro = (
            "Thank you for planning your Sri Lanka trip with LeafyMind. "
            f"I hope {package_name} helped shape a stay you'll love."
            if is_planning
            else (
                "Thank you so much for choosing Leafy Cave for your Sri Lanka adventure. "
                f"I hope {package_name} gave you memories you'll carry for a long time "
                f"during your {nights}-night stay."
            )
        )
        ask = (
            "Could you take just 2 minutes to tell us how the AI planning experience went? "
            "Your feedback helps us improve LeafyMind for future guests."
            if is_planning
            else (
                "Your experience means everything to us. Could you take just 2 minutes "
                "to share how your stay went? Your honest feedback helps us make the "
                "experience even better for the next guest."
            )
        )

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Georgia, serif; background: #f5f0e8; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 0 auto; background: white; }}
    .header {{ background: #1a4731; padding: 40px; text-align: center; }}
    .header h1 {{ color: #c9a84c; font-size: 28px; margin: 0; letter-spacing: 2px; }}
    .header p {{ color: #f5f0e8; margin: 8px 0 0; font-size: 14px; }}
    .body {{ padding: 40px; color: #333; line-height: 1.8; }}
    .body h2 {{ color: #1a4731; }}
    .cta-button {{
      display: inline-block; background: #c9a84c; color: #1a4731;
      padding: 16px 32px; text-decoration: none; border-radius: 4px;
      font-size: 16px; margin: 24px 0; letter-spacing: 1px; font-weight: bold;
    }}
    .footer {{ background: #1a4731; padding: 20px; text-align: center;
               color: #f5f0e8; font-size: 12px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🌿 LEAFY CAVE</h1>
      <p>Wellawaya, Sri Lanka</p>
    </div>
    <div class="body">
      <h2>Dear {name},</h2>
      <p>{intro}</p>
      <p>{ask}</p>
      <p style="text-align: center;">
        <a href="{feedback_url}" class="cta-button">Share My Experience 🌿</a>
      </p>
      <p>
        With warmth,<br>
        <strong>Pramitha Madushanka</strong><br>
        <em>Owner, Leafy Cave Cabana</em>
      </p>
    </div>
    <div class="footer">
      Leafy Cave Luxury Cabana · Wellawaya, Sri Lanka<br>
      You received this because you stayed with us.
    </div>
  </div>
</body>
</html>"""

    def _build_feedback_email_plain(
        self,
        name: str,
        session_id: str,
        summary: dict[str, Any],
        *,
        feedback_path: str | None = None,
    ) -> str:
        feedback_url = self._feedback_url(session_id, feedback_path)
        package_name = summary.get("package_name", "your Leafy Cave experience")
        is_planning = feedback_path and "/agents/" in feedback_path
        if is_planning:
            body_intro = (
                f"Thank you for using LeafyMind to plan your trip.\n\n"
                f"We hope {package_name} was helpful.\n\n"
                "Please take 2 minutes to share how the planning experience went:"
            )
        else:
            body_intro = (
                "Thank you for staying at Leafy Cave, Wellawaya.\n\n"
                f"We hope {package_name} made your Sri Lanka trip special.\n\n"
                "We would love to hear about your experience. Please take 2 minutes "
                "to share your feedback here:"
            )
        return f"""Dear {name},

{body_intro}
{feedback_url}

With warmth,
Pramitha Madushanka
Owner, Leafy Cave Cabana
"""


email_service = EmailService()
