"""Auth I/O schemas (contract tag `auth`)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.auth.email import normalize_email, validate_and_normalize_email
from app.modules.users.schemas import Locale, UserOut

ClientPlatform = Literal["web", "native"]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    # Real length rules live in password_policy (WEAK_PASSWORD with a reason).
    password: str = Field(max_length=1024)
    locale: Locale = "vi"

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return validate_and_normalize_email(value)


class LoginRequest(BaseModel):
    """No email syntax check: a malformed email is simply "not found"."""

    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)
    password: str = Field(max_length=1024)


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str | None = Field(default=None, max_length=512)


class AuthSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user: UserOut
    # Native only; web gets httpOnly cookies (R12).
    access_token: str | None = None
    refresh_token: str | None = None
    access_token_expires_in: int


# ---------- email codes (docs/specs/f4-email-codes.md) ----------

CODE_PATTERN = r"^\s*\d{6}\s*$"


class VerifyEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(pattern=CODE_PATTERN)


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetConfirmRequest(PasswordResetRequest):
    code: str = Field(pattern=CODE_PATTERN)
    new_password: str = Field(max_length=1024)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(max_length=1024)
    new_password: str = Field(max_length=1024)
