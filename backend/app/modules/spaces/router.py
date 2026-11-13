"""Router for spaces (contract tag `spaces`)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.object_storage import ObjectStorage, get_storage
from app.modules.auth.dependencies import get_current_user
from app.modules.documents.queue import JobQueue, get_job_queue
from app.modules.documents.service import DocumentService
from app.modules.spaces.schemas import SpaceListOut, SpaceNameRequest, SpaceOut
from app.modules.spaces.service import SpaceService
from app.modules.users.models import User

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]


@router.get("", response_model=SpaceListOut, operation_id="listSpaces")
async def list_spaces(user: CurrentUser, db: Db) -> SpaceListOut:
    spaces = await SpaceService(db).list(user.id)
    return SpaceListOut(items=[SpaceOut.model_validate(s) for s in spaces])


@router.post(
    "",
    response_model=SpaceOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="createSpace",
)
async def create_space(body: SpaceNameRequest, user: CurrentUser, db: Db) -> SpaceOut:
    return SpaceOut.model_validate(await SpaceService(db).create(user.id, body.name))


@router.get("/{space_id}", response_model=SpaceOut, operation_id="getSpace")
async def get_space(space_id: uuid.UUID, user: CurrentUser, db: Db) -> SpaceOut:
    return SpaceOut.model_validate(await SpaceService(db).get(user.id, space_id))


@router.patch("/{space_id}", response_model=SpaceOut, operation_id="renameSpace")
async def rename_space(
    space_id: uuid.UUID, body: SpaceNameRequest, user: CurrentUser, db: Db
) -> SpaceOut:
    return SpaceOut.model_validate(await SpaceService(db).rename(user.id, space_id, body.name))


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteSpace")
async def delete_space(
    space_id: uuid.UUID,
    user: CurrentUser,
    db: Db,
    queue: Annotated[JobQueue, Depends(get_job_queue)],
    storage: Annotated[ObjectStorage, Depends(get_storage)],
) -> Response:
    # Purges the documents' files too (spec f6), then removes the space.
    await DocumentService(db, storage, queue).delete_space(user.id, space_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
