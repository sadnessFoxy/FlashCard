"""
Email service (Mailpit cho local dev, real SMTP cho production).
R3: SMTP credentials come from env vars.
R10: never log email bodies or tokens.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """
    Send email over SMTP.
    Local dev uses Mailpit (port 1025).
    """

    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
    ) -> None:
        """Send the account verification email."""
        # TODO(F4): implement with aiosmtplib
        # verification_token is the plaintext token for the user;
        # only its hash is stored (R15)
        logger.info("Sending verification email to %s", to_email)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
    ) -> None:
        """Send the password reset email."""
        # TODO(F4): implement
        # R15: single-use, expiring, stored hashed
        logger.info("Sending password reset email to %s", to_email)

    async def send_security_alert(
        self,
        to_email: str,
        event: str,
    ) -> None:
        """Send a security alert (password changed, unusual sign-in)."""
        # TODO(phase 4): implement
        logger.info("Sending security alert '%s' to %s", event, to_email)


email_service = EmailService()
