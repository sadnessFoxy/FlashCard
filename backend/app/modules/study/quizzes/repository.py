"""Data access for quizzes, always scoped to the owner (R4)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.study.quizzes.models import Quiz, QuizAttempt, QuizQuestion


@dataclass(frozen=True)
class QuizStats:
    question_count: int = 0
    attempt_count: int = 0
    last_score: int | None = None


class QuizRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_quizzes(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[Quiz]:
        result = await self._session.execute(
            select(Quiz)
            .where(Quiz.owner_id == owner_id, Quiz.space_id == space_id)
            .order_by(Quiz.created_at.desc())
        )
        return list(result.scalars())

    async def get_quiz(self, owner_id: uuid.UUID, quiz_id: uuid.UUID) -> Quiz | None:
        result = await self._session.execute(
            select(Quiz).where(Quiz.id == quiz_id, Quiz.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def questions(self, quiz_id: uuid.UUID) -> list[QuizQuestion]:
        result = await self._session.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.position)
        )
        return list(result.scalars())

    async def stats(self, quiz_ids: list[uuid.UUID]) -> dict[uuid.UUID, QuizStats]:
        if not quiz_ids:
            return {}
        questions = dict(
            (
                await self._session.execute(
                    select(QuizQuestion.quiz_id, func.count())
                    .where(QuizQuestion.quiz_id.in_(quiz_ids))
                    .group_by(QuizQuestion.quiz_id)
                )
            ).all()
        )
        attempts = dict(
            (
                await self._session.execute(
                    select(QuizAttempt.quiz_id, func.count())
                    .where(QuizAttempt.quiz_id.in_(quiz_ids))
                    .group_by(QuizAttempt.quiz_id)
                )
            ).all()
        )
        latest = (
            select(QuizAttempt.quiz_id, QuizAttempt.score)
            .where(QuizAttempt.quiz_id.in_(quiz_ids))
            .distinct(QuizAttempt.quiz_id)
            .order_by(QuizAttempt.quiz_id, QuizAttempt.created_at.desc())
        )
        last_scores = dict((await self._session.execute(latest)).all())
        return {
            q: QuizStats(int(questions.get(q, 0)), int(attempts.get(q, 0)), last_scores.get(q))
            for q in quiz_ids
        }

    async def delete_quiz(self, quiz: Quiz) -> None:
        # Questions and attempts go with it (ON DELETE CASCADE).
        await self._session.execute(
            delete(Quiz).where(Quiz.id == quiz.id, Quiz.owner_id == quiz.owner_id)
        )

    async def add(self, *objects: Quiz | QuizQuestion | QuizAttempt) -> None:
        self._session.add_all(objects)
        await self._session.flush()
