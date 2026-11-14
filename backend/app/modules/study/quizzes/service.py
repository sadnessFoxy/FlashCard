"""
Quizzes (U13): the AI writes questions from a document or page range; grading is done by
code, never by the AI. Correct answers are only returned with an attempt's results.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AiTemporarilyUnavailableError, NotFoundError
from app.core.logging import get_logger
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.spaces.service import SpaceService
from app.modules.study.flashcards.repository import FlashcardRepository
from app.modules.study.flashcards.schemas import CardSourceOut
from app.modules.study.quizzes.models import Quiz, QuizAttempt, QuizQuestion
from app.modules.study.quizzes.prompts import (
    SYSTEM_PROMPT,
    DraftQuestion,
    build_request,
    parse_questions,
)
from app.modules.study.quizzes.repository import QuizRepository, QuizStats
from app.modules.study.quizzes.schemas import (
    AnswerIn,
    AttemptResultOut,
    CreateQuizRequest,
    QuestionOut,
    QuestionResultOut,
    QuizDetailOut,
    QuizSummaryOut,
)
from app.modules.study.source_material import SourceMaterial, SourceMaterialLoader
from app.modules.usage.quota import QuizQuota

logger = get_logger(__name__)

GENERATION_TEMPERATURE = 0.4


class QuizService:
    def __init__(self, session: AsyncSession, gateway: LLMGateway, quota: QuizQuota) -> None:
        self._session = session
        self._repo = QuizRepository(session)
        self._gateway = gateway
        self._quota = quota

    # ---------- create ----------

    async def create(self, owner_id: uuid.UUID, request: CreateQuizRequest) -> QuizDetailOut:
        await SpaceService(self._session).get(owner_id, request.space_id)
        await self._quota.require(owner_id)
        material = await SourceMaterialLoader(
            self._session, settings.QUIZ_SOURCE_CHARS
        ).from_document(
            owner_id, request.space_id, request.document_id, request.page_start, request.page_end
        )
        drafts = await self._quota.spend(
            owner_id, lambda: self._generate(owner_id, material, request.question_count)
        )
        quiz = Quiz(
            owner_id=owner_id,
            space_id=request.space_id,
            title=material.passages[0].document_name,
            source_document_id=request.document_id,
            source_document_name=material.passages[0].document_name,
            page_start=request.page_start,
            page_end=request.page_end,
        )
        await self._repo.add(quiz)
        questions = [_question(quiz.id, i, d, material) for i, d in enumerate(drafts)]
        await self._repo.add(*questions)
        await self._session.refresh(quiz)
        stats = QuizStats(question_count=len(questions))
        return _detail(quiz, stats, questions)

    async def _generate(
        self, owner_id: uuid.UUID, material: SourceMaterial, count: int
    ) -> list[DraftQuestion]:
        raw = await self._gateway.generate(
            build_request(material.passages, count),
            system_prompt=SYSTEM_PROMPT,
            max_tokens=settings.QUIZ_MAX_OUTPUT_TOKENS,
            temperature=GENERATION_TEMPERATURE,
            response_format={"type": "json_object"},
            user_id=str(owner_id),
        )
        drafts = parse_questions(raw, len(material.passages), count)
        if not drafts:
            logger.warning("Quiz output was unusable (%d chars)", len(raw))
            raise AiTemporarilyUnavailableError()
        return drafts

    # ---------- read and delete ----------

    async def list_quizzes(self, owner_id: uuid.UUID, space_id: uuid.UUID) -> list[QuizSummaryOut]:
        await SpaceService(self._session).get(owner_id, space_id)
        quizzes = await self._repo.list_quizzes(owner_id, space_id)
        stats = await self._repo.stats([q.id for q in quizzes])
        return [_summary(q, stats[q.id]) for q in quizzes]

    async def get(self, owner_id: uuid.UUID, quiz_id: uuid.UUID) -> QuizDetailOut:
        quiz = await self._require(owner_id, quiz_id)
        stats = await self._repo.stats([quiz.id])
        return _detail(quiz, stats[quiz.id], await self._repo.questions(quiz.id))

    async def delete(self, owner_id: uuid.UUID, quiz_id: uuid.UUID) -> None:
        await self._repo.delete_quiz(await self._require(owner_id, quiz_id))

    # ---------- grading ----------

    async def submit(
        self, owner_id: uuid.UUID, quiz_id: uuid.UUID, answers: list[AnswerIn]
    ) -> AttemptResultOut:
        """Unanswered or unknown questions count as wrong; the score is computed here."""
        quiz = await self._require(owner_id, quiz_id)
        questions = await self._repo.questions(quiz.id)
        chosen = {a.question_id: a.choice for a in answers}
        choices = {q.id: _valid_choice(chosen.get(q.id), q) for q in questions}
        score = sum(1 for q in questions if choices[q.id] == q.correct_index)

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            owner_id=owner_id,
            answers={str(k): v for k, v in choices.items()},
            score=score,
            total=len(questions),
        )
        await self._repo.add(attempt)
        await self._session.refresh(attempt)
        source_live = await self._source_exists(owner_id, quiz)
        return AttemptResultOut(
            id=attempt.id,
            quiz_id=quiz.id,
            score=score,
            total=len(questions),
            created_at=attempt.created_at,
            results=[_result(q, choices[q.id], quiz, source_live) for q in questions],
        )

    async def _require(self, owner_id: uuid.UUID, quiz_id: uuid.UUID) -> Quiz:
        quiz = await self._repo.get_quiz(owner_id, quiz_id)
        if quiz is None:
            raise NotFoundError("Quiz")
        return quiz

    async def _source_exists(self, owner_id: uuid.UUID, quiz: Quiz) -> bool:
        if quiz.source_document_id is None:
            return False
        found = await FlashcardRepository(self._session).owned_documents(
            owner_id, {quiz.source_document_id}
        )
        return quiz.source_document_id in found


def _question(
    quiz_id: uuid.UUID, position: int, draft: DraftQuestion, material: SourceMaterial
) -> QuizQuestion:
    passage = material.passages[draft.source_index - 1] if draft.source_index else None
    return QuizQuestion(
        quiz_id=quiz_id,
        position=position,
        prompt=draft.prompt,
        options=draft.options,
        correct_index=draft.correct_index,
        explanation=draft.explanation,
        source_page=passage.page_start if passage else None,
    )


def _valid_choice(choice: int | None, question: QuizQuestion) -> int | None:
    return choice if choice is not None and 0 <= choice < len(question.options) else None


def _summary(quiz: Quiz, stats: QuizStats) -> QuizSummaryOut:
    return QuizSummaryOut(
        id=quiz.id,
        space_id=quiz.space_id,
        title=quiz.title,
        page_start=quiz.page_start,
        page_end=quiz.page_end,
        question_count=stats.question_count,
        attempt_count=stats.attempt_count,
        last_score=stats.last_score,
        created_at=quiz.created_at,
    )


def _detail(quiz: Quiz, stats: QuizStats, questions: list[QuizQuestion]) -> QuizDetailOut:
    return QuizDetailOut(
        **_summary(quiz, stats).model_dump(),
        questions=[
            QuestionOut(id=q.id, position=q.position, prompt=q.prompt, options=q.options)
            for q in questions
        ],
    )


def _result(
    question: QuizQuestion, choice: int | None, quiz: Quiz, source_live: bool
) -> QuestionResultOut:
    return QuestionResultOut(
        question_id=question.id,
        prompt=question.prompt,
        options=question.options,
        choice=choice,
        correct_index=question.correct_index,
        is_correct=choice == question.correct_index,
        explanation=question.explanation,
        source=CardSourceOut(
            document_id=quiz.source_document_id if source_live else None,
            document_name=quiz.source_document_name,
            page=question.source_page,
        ),
    )
