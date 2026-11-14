"""Quiz I/O schemas (contract tag `quizzes`). Correct answers appear only in attempt results."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.modules.study.flashcards.schemas import CardSourceOut


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateQuizRequest(_Strict):
    space_id: uuid.UUID
    document_id: uuid.UUID
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    question_count: int = Field(default=10, ge=1, le=settings.QUIZ_MAX_QUESTIONS)


class QuizSummaryOut(_Strict):
    id: uuid.UUID
    space_id: uuid.UUID
    title: str
    page_start: int | None
    page_end: int | None
    question_count: int
    attempt_count: int
    last_score: int | None
    created_at: datetime


class QuizListOut(_Strict):
    items: list[QuizSummaryOut]


class QuestionOut(_Strict):
    """What the learner sees while answering: no correct answer, no explanation."""

    id: uuid.UUID
    position: int
    prompt: str
    options: list[str]


class QuizDetailOut(QuizSummaryOut):
    questions: list[QuestionOut]


class AnswerIn(_Strict):
    question_id: uuid.UUID
    choice: int | None = Field(default=None, ge=0, description="Null when left blank")


class SubmitAttemptRequest(_Strict):
    answers: list[AnswerIn] = Field(max_length=settings.QUIZ_MAX_QUESTIONS)


class QuestionResultOut(_Strict):
    question_id: uuid.UUID
    prompt: str
    options: list[str]
    choice: int | None
    correct_index: int
    is_correct: bool
    explanation: str
    source: CardSourceOut | None


class AttemptResultOut(_Strict):
    id: uuid.UUID
    quiz_id: uuid.UUID
    score: int
    total: int
    created_at: datetime
    results: list[QuestionResultOut]
