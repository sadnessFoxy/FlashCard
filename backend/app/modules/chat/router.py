"""Router for conversations and Q&A (contract tag `chat`)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import StreamingResponse

from app.modules.auth.dependencies import get_current_user
from app.modules.chat.dependencies import get_chat_service
from app.modules.chat.schemas import (
    ConversationDetailOut,
    ConversationListOut,
    ConversationOut,
    CreateConversationRequest,
    SendMessageRequest,
)
from app.modules.chat.service import ChatService
from app.modules.users.models import User

router = APIRouter()

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[ChatService, Depends(get_chat_service)]


@router.post(
    "",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="createConversation",
)
async def create_conversation(
    body: CreateConversationRequest, user: CurrentUser, service: Service
) -> ConversationOut:
    conversation = await service.create_conversation(user.id, body.space_id)
    return ConversationOut.model_validate(conversation)


@router.get("", response_model=ConversationListOut, operation_id="listConversations")
async def list_conversations(
    user: CurrentUser,
    service: Service,
    space_id: Annotated[uuid.UUID, Query()],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> ConversationListOut:
    items = await service.list_conversations(user.id, space_id, limit)
    return ConversationListOut(items=[ConversationOut.model_validate(c) for c in items])


@router.get(
    "/{conversation_id}", response_model=ConversationDetailOut, operation_id="getConversation"
)
async def get_conversation(
    conversation_id: uuid.UUID, user: CurrentUser, service: Service
) -> ConversationDetailOut:
    conversation, messages = await service.get_conversation(user.id, conversation_id)
    base = ConversationOut.model_validate(conversation)
    return ConversationDetailOut(**base.model_dump(), messages=messages)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteConversation",
)
async def delete_conversation(
    conversation_id: uuid.UUID, user: CurrentUser, service: Service
) -> Response:
    await service.delete_conversation(user.id, conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{conversation_id}/messages",
    operation_id="sendMessage",
    response_class=StreamingResponse,
)
async def send_message(
    conversation_id: uuid.UUID, body: SendMessageRequest, user: CurrentUser, service: Service
) -> StreamingResponse:
    # Errors raised here (404, quota, AI down while embedding) are normal JSON responses.
    turn = await service.prepare(user.id, conversation_id, body.content, body.document_ids)
    return StreamingResponse(
        service.stream(turn),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
