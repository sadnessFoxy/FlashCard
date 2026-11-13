"""
Outgoing email over SMTP (Mailpit locally, a real SMTP server later).
R3: credentials come from settings. R10: bodies and codes are never logged.
"""

from __future__ import annotations

import asyncio
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    text: str


class Mailer(Protocol):
    async def send(self, email: OutgoingEmail) -> None: ...


class SmtpMailer:
    """Sends with the standard library in a worker thread so the event loop never blocks."""

    async def send(self, email: OutgoingEmail) -> None:
        await asyncio.to_thread(self._send_sync, email)

    @staticmethod
    def _send_sync(email: OutgoingEmail) -> None:
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = email.to
        message["Subject"] = email.subject
        message.set_content(email.text)
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USERNAME:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)


_mailer: Mailer = SmtpMailer()


def get_mailer() -> Mailer:
    return _mailer


async def send_quietly(mailer: Mailer, email: OutgoingEmail, purpose: str) -> bool:
    """Send; on failure log the purpose only (no address, no body) and report False."""
    try:
        await mailer.send(email)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        logger.warning("Email not sent (purpose=%s, error=%s)", purpose, type(exc).__name__)
        return False
