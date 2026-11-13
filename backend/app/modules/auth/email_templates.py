"""Account emails in the user's language (vi, en). Plain text: no tracking, no remote images."""

from __future__ import annotations

from app.core.config import settings
from app.integrations.email import OutgoingEmail

_TEXTS: dict[str, dict[str, tuple[str, str]]] = {
    "verify": {
        "vi": (
            "Mã xác minh email FlashCard: {code}",
            "Mã xác minh email của bạn là: {code}\n\n"
            "Mã có hiệu lực trong {minutes} phút. "
            "Nếu bạn không đăng ký FlashCard, hãy bỏ qua email này.",
        ),
        "en": (
            "Your FlashCard verification code: {code}",
            "Your email verification code is: {code}\n\n"
            "It expires in {minutes} minutes. "
            "If you didn't sign up for FlashCard, ignore this email.",
        ),
    },
    "reset": {
        "vi": (
            "Mã đặt lại mật khẩu FlashCard: {code}",
            "Mã đặt lại mật khẩu của bạn là: {code}\n\n"
            "Mã có hiệu lực trong {minutes} phút. Nếu bạn không yêu cầu, hãy bỏ qua email này; "
            "mật khẩu của bạn không thay đổi.",
        ),
        "en": (
            "Your FlashCard password reset code: {code}",
            "Your password reset code is: {code}\n\n"
            "It expires in {minutes} minutes. If you didn't ask for this, ignore this email; "
            "your password stays the same.",
        ),
    },
    "google_only": {
        "vi": (
            "Đăng nhập FlashCard bằng Google",
            "Tài khoản của bạn dùng đăng nhập bằng Google nên không có mật khẩu để đặt lại.\n\n"
            'Hãy chọn "Đăng nhập bằng Google" trên màn hình đăng nhập.',
        ),
        "en": (
            "Sign in to FlashCard with Google",
            "Your account signs in with Google, so there is no password to reset.\n\n"
            'Choose "Sign in with Google" on the sign-in screen.',
        ),
    },
    "password_changed": {
        "vi": (
            "Mật khẩu FlashCard đã được đổi",
            "Mật khẩu tài khoản FlashCard của bạn vừa được đổi "
            "và mọi phiên đăng nhập cũ đã bị đăng xuất.\n\n"
            "Nếu không phải bạn, hãy đặt lại mật khẩu ngay.",
        ),
        "en": (
            "Your FlashCard password was changed",
            "Your FlashCard password was just changed and all other sessions were signed out.\n\n"
            "If this wasn't you, reset your password right away.",
        ),
    },
}


def account_email(kind: str, to: str, locale: str, code: str = "") -> OutgoingEmail:
    subject, body = _TEXTS[kind].get(locale, _TEXTS[kind]["vi"])
    values = {"code": code, "minutes": settings.AUTH_CODE_TTL_MINUTES}
    return OutgoingEmail(to=to, subject=subject.format(**values), text=body.format(**values))
