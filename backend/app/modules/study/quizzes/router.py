"""Router for quizzes (/v1/quizzes), contract tag `quizzes`."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.llm_gateway.dependency import get_gateway
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.auth.dependencies import get_current_user
from app.modules.study.quizzes.schemas import (
    AttemptResultOut,
    CreateQuizRequest,
    QuizDetailOut,
    QuizListOut,
    SubmitAttemptRequest,
)
from app.modules.study.quizzes.service import QuizService
from app.modules.usage.quota import QuizQuota, get_quiz_quota
from app.modules.users.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[AsyncSession, Depends(get_db, scope="function")]

router = APIRouter()


def get_quiz_service(
    db: Db,
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
    quota: Annotated[QuizQuota, Depends(get_quiz_quota)],
) -> QuizService:
    return QuizService(db, gateway, quota)


Service = Annotated[QuizService, Depends(get_quiz_service)]


@router.post(
    "", response_model=QuizDetailOut, status_code=status.HTTP_201_CREATED, operation_id="createQuiz"
)
async def create_quiz(
    body: CreateQuizRequest, user: CurrentUser, service: Service
) -> QuizDetailOut:
    return await service.create(user.id, body)


@router.get("", response_model=QuizListOut, operation_id="listQuizzes")
async def list_quizzes(
    user: CurrentUser, service: Service, space_id: Annotated[uuid.UUID, Query()]
) -> QuizListOut:
    return QuizListOut(items=await service.list_quizzes(user.id, space_id))


@router.get("/{quiz_id}", response_model=QuizDetailOut, operation_id="getQuiz")
async def get_quiz(quiz_id: uuid.UUID, user: CurrentUser, service: Service) -> QuizDetailOut:
    return await service.get(user.id, quiz_id)


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="deleteQuiz")
async def delete_quiz(quiz_id: uuid.UUID, user: CurrentUser, service: Service) -> Response:
    await service.delete(user.id, quiz_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{quiz_id}/attempts",
    response_model=AttemptResultOut,
    status_code=status.HTTP_201_CREATED,
    operation_id="submitQuizAttempt",
)
async def submit_attempt(
    quiz_id: uuid.UUID, body: SubmitAttemptRequest, user: CurrentUser, service: Service
) -> AttemptResultOut:
    """Graded by code; the response is the only place correct answers appear."""
    return await service.submit(user.id, quiz_id, body.answers)
