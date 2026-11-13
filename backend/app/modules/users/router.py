"""Router for the signed-in user (contract tag `users`)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.modules.auth.cookies import clear_session_cookies
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import ClientPlatform
from app.modules.documents.queue import JobQueue, get_job_queue
from app.modules.users.account_deletion import AccountDeletion
from app.modules.users.models import User
from app.modules.users.schemas import (
    ConsentListOut,
    ConsentOut,
    ConsentRequest,
    DeleteAccountRequest,
    UpdateMeRequest,
    UserOut,
)
from app.modules.users.service import UserService

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]


def _current_versions() -> dict[str, str]:
    return {"ai_processing": settings.AI_CONSENT_VERSION}


@router.get("/me", response_model=UserOut, operation_id="getMe")
async def get_me(user: CurrentUser) -> UserOut:
    """The signed-in user."""
    return UserOut.from_model(user)


@router.get("/me/consents", response_model=ConsentListOut, operation_id="listMyConsents")
async def list_consents(user: CurrentUser, db: Db) -> ConsentListOut:
    consents = await UserService(db).consents(user.id)
    return ConsentListOut(
        items=[ConsentOut.model_validate(c) for c in consents],
        current_versions=_current_versions(),
    )


@router.post(
    "/me/consents",
    response_model=ConsentOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="giveConsent",
)
async def give_consent(
    body: ConsentRequest, response: Response, user: CurrentUser, db: Db
) -> ConsentOut:
    # Only the current notice can be accepted: consent to an old text proves nothing.
    if body.version != _current_versions()[body.kind]:
        raise ValidationError(
            "Consent version is not current", {"current_version": _current_versions()[body.kind]}
        )
    consent, created = await UserService(db).give_consent(user.id, body.kind, body.version)
    if not created:
        response.status_code = status.HTTP_200_OK
    return ConsentOut.model_validate(consent)


@router.patch("/me", response_model=UserOut, operation_id="updateMe")
async def update_me(body: UpdateMeRequest, user: CurrentUser, db: Db) -> UserOut:
    """Interface language, kept per account (U10)."""
    return UserOut.from_model(await UserService(db).update_locale(user, body.locale))


@router.post("/me/deletion", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteMe")
async def delete_me(
    body: DeleteAccountRequest,
    user: CurrentUser,
    db: Db,
    queue: Annotated[JobQueue, Depends(get_job_queue)],
    platform: Annotated[ClientPlatform, Header(alias="X-Client-Platform")],
) -> Response:
    """Permanently delete the account and everything in it (U9)."""
    await AccountDeletion(db, queue).delete(
        user, password=body.password, confirm_email=body.confirm_email
    )
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if platform == "web":
        clear_session_cookies(response)
    return response
