"""Router cho module auth (contract/openapi.yaml, tag `auth`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import app_error_handler
from app.core.exceptions import AppError, InvalidRefreshTokenError
from app.core.security import access_token_ttl_seconds
from app.db.session import get_db
from app.integrations.email import Mailer, get_mailer, send_quietly
from app.modules.auth.cookies import REFRESH_COOKIE, clear_session_cookies, set_session_cookies
from app.modules.auth.dependencies import get_client_info, get_current_user
from app.modules.auth.email_templates import account_email
from app.modules.auth.password_reset import PasswordReset
from app.modules.auth.schemas import (
    AuthSessionOut,
    ChangePasswordRequest,
    ClientPlatform,
    LoginRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    RefreshTokenRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from app.modules.auth.service import AuthService, ClientInfo, IssuedSession
from app.modules.auth.verification import EmailVerification
from app.modules.users.models import User
from app.modules.users.schemas import UserOut

router = APIRouter()

PlatformHeader = Annotated[ClientPlatform, Header(alias="X-Client-Platform")]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]
Client = Annotated[ClientInfo, Depends(get_client_info)]
Mail = Annotated[Mailer, Depends(get_mailer)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def _session_response(
    issued: IssuedSession, platform: ClientPlatform, response: Response
) -> AuthSessionOut:
    out = AuthSessionOut(
        user=UserOut.from_model(issued.user),
        access_token_expires_in=access_token_ttl_seconds(),
    )
    if platform == "native":
        out.access_token = issued.access_token
        out.refresh_token = issued.refresh_token
    else:
        set_session_cookies(
            response,
            access_token=issued.access_token,
            refresh_token=issued.refresh_token,
            refresh_expires_at=issued.refresh_expires_at,
        )
    return out


def _refresh_token_from(
    request: Request, platform: ClientPlatform, body: RefreshTokenRequest | None
) -> str | None:
    if platform == "web":
        return request.cookies.get(REFRESH_COOKIE)
    return body.refresh_token if body else None


@router.post(
    "/register",
    response_model=AuthSessionOut,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
    operation_id="register",
)
async def register(
    body: RegisterRequest,
    platform: PlatformHeader,
    response: Response,
    db: Db,
    client: Client,
    mailer: Mail,
) -> AuthSessionOut:
    issued = await AuthService(db).register(
        email=body.email, password=body.password, locale=body.locale, client=client
    )
    await EmailVerification(db, mailer).send(issued.user)
    return _session_response(issued, platform, response)


@router.post(
    "/login",
    response_model=AuthSessionOut,
    response_model_exclude_none=True,
    operation_id="login",
)
async def login(
    body: LoginRequest, platform: PlatformHeader, response: Response, db: Db, client: Client
) -> AuthSessionOut:
    issued = await AuthService(db).login(email=body.email, password=body.password, client=client)
    return _session_response(issued, platform, response)


@router.post(
    "/refresh",
    response_model=AuthSessionOut,
    response_model_exclude_none=True,
    operation_id="refreshSession",
)
async def refresh_session(
    request: Request,
    platform: PlatformHeader,
    response: Response,
    db: Db,
    client: Client,
    body: RefreshTokenRequest | None = None,
) -> AuthSessionOut | JSONResponse:
    token = _refresh_token_from(request, platform, body)
    try:
        if not token:
            raise InvalidRefreshTokenError()
        issued = await AuthService(db).refresh(refresh_token=token, client=client)
    except AppError as exc:
        # Web: drop dead session cookies so the browser stops sending them.
        error = await app_error_handler(request, exc)
        if platform == "web":
            clear_session_cookies(error)
        return error
    return _session_response(issued, platform, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, operation_id="logout")
async def logout(
    request: Request,
    platform: PlatformHeader,
    db: Db,
    body: RefreshTokenRequest | None = None,
) -> Response:
    await AuthService(db).logout(refresh_token=_refresh_token_from(request, platform, body))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if platform == "web":
        clear_session_cookies(response)
    return response


# ---------- email codes (docs/specs/f4-email-codes.md) ----------


@router.post(
    "/email-verification",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="sendEmailVerification",
)
async def send_email_verification(user: CurrentUser, db: Db, mailer: Mail) -> Response:
    await EmailVerification(db, mailer).send(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/email-verification/confirm", response_model=UserOut, operation_id="confirmEmailVerification"
)
async def confirm_email_verification(
    body: VerifyEmailRequest, user: CurrentUser, db: Db, mailer: Mail
) -> UserOut:
    return UserOut.from_model(await EmailVerification(db, mailer).confirm(user, body.code))


@router.post(
    "/password-reset", status_code=status.HTTP_202_ACCEPTED, operation_id="requestPasswordReset"
)
async def request_password_reset(
    body: PasswordResetRequest, db: Db, client: Client, mailer: Mail
) -> Response:
    # Same answer whether or not the email exists (no account enumeration).
    await PasswordReset(db, mailer).request(body.email, client.ip)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="confirmPasswordReset",
)
async def confirm_password_reset(
    body: PasswordResetConfirmRequest, db: Db, mailer: Mail
) -> Response:
    await PasswordReset(db, mailer).reset(body.email, body.code, body.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/password/change",
    response_model=AuthSessionOut,
    response_model_exclude_none=True,
    operation_id="changePassword",
)
async def change_password(
    body: ChangePasswordRequest,
    user: CurrentUser,
    platform: PlatformHeader,
    response: Response,
    db: Db,
    client: Client,
    mailer: Mail,
) -> AuthSessionOut:
    """Every other session is signed out; this device gets a fresh session."""
    issued = await AuthService(db).change_password(
        user=user,
        current_password=body.current_password,
        new_password=body.new_password,
        client=client,
    )
    alert = account_email("password_changed", user.email, user.locale)
    await send_quietly(mailer, alert, "password_changed")
    return _session_response(issued, platform, response)
