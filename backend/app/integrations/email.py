"""
Email service (Mailpit cho local dev, real SMTP cho production).
Tuân thủ R3: SMTP credentials từ env vars.
Tuân thủ R10: không log nội dung email nhạy cảm.
"""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """
    Gửi email qua SMTP.
    Dùng Mailpit (port 1025) ở local dev.
    """

    async def send_verification_email(
        self,
        to_email: str,
        verification_token: str,
    ) -> None:
        """Gửi email xác minh tài khoản."""
        # TODO (giai đoạn F4): implement với aiosmtplib
        # Lưu ý: verification_token là plaintext token gửi cho user
        # Backend chỉ lưu hash của token (R15)
        logger.info("Sending verification email to %s", to_email)

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
    ) -> None:
        """Gửi email đặt lại mật khẩu."""
        # TODO (giai đoạn F4): implement
        # R15: token một lần, có hạn, chỉ lưu hash ở DB
        logger.info("Sending password reset email to %s", to_email)

    async def send_security_alert(
        self,
        to_email: str,
        event: str,
    ) -> None:
        """Gửi email cảnh báo bảo mật (đổi mật khẩu, đăng nhập lạ)."""
        # TODO (giai đoạn 4): implement
        logger.info("Sending security alert '%s' to %s", event, to_email)


email_service = EmailService()
