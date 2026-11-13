"""FastAPI dependencies for the chat module."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.chat.service import ChatService
from app.modules.usage.quota import QuestionQuota, get_question_quota


def get_chat_service(
    db: Annotated[AsyncSession, Depends(get_db, scope="function")],
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
    quota: Annotated[QuestionQuota, Depends(get_question_quota)],
) -> ChatService:
    return ChatService(db, gateway, quota)
