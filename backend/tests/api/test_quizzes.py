"""F11 acceptance criteria (docs/specs/f11-quizzes.md section 9)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from httpx import AsyncClient, Response
from sqlalchemy import delete

from app.core.config import settings
from app.core.exceptions import AiQuotaExhaustedError
from app.core.redis import get_redis
from app.db.session import AsyncSessionLocal
from app.modules.documents.models import Document
from app.modules.documents.states import PROCESSING
from app.modules.usage.quota import QuizQuota
from tests.contract_schema import assert_response_matches_contract
from tests.fixtures.chat import Reader, TopicProvider, ai, new_reader, seed_document

__all__ = ["ai"]  # pytest fixture, imported for use by the tests below

pytestmark = pytest.mark.usefixtures("clean_db")


async def call(client: AsyncClient, method: str, url: str, reader: Reader, **kw: Any) -> Response:
    response = await client.request(method, url, headers=reader.auth, **kw)
    assert_response_matches_contract(response)
    return response


def questions_json(*items: tuple[str, list[str], int, int]) -> str:
    return json.dumps(
        {
            "questions": [
                {
                    "question": q,
                    "options": o,
                    "answer": a,
                    "explanation": f"Because {q}",
                    "source": s,
                }
                for q, o, a, s in items
            ]
        }
    )


OPTIONS = ["Slope of the tangent", "Area under the curve", "A limit at infinity", "A matrix"]


async def create(
    client: AsyncClient, reader: Reader, document_id: object, **extra: Any
) -> Response:
    return await call(
        client,
        "POST",
        "/v1/quizzes",
        reader,
        json={"space_id": reader.space_id, "document_id": str(document_id), **extra},
    )


def correct(detail_question: dict[str, Any]) -> int:
    return detail_question["options"].index("Slope of the tangent")


# 1. A quiz is written from the chosen pages; answers are never shown before submitting.
async def test_create_quiz_hides_answers(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(
        reader,
        "Giải tích.pdf",
        [(1, "Limits."), (2, "A derivative is the slope."), (3, "Integrals.")],
    )
    ai.generate_script = [questions_json(("What is a derivative?", OPTIONS, 0, 1))]

    response = await create(client, reader, doc, page_start=2, page_end=2, question_count=5)

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Giải tích.pdf" and body["page_start"] == 2
    [question] = body["questions"]
    assert sorted(question["options"]) == sorted(OPTIONS)
    assert "correct_index" not in question and "explanation" not in question
    prompt = ai.generate_calls[0]["prompt"]
    assert "A derivative is the slope." in prompt and "Integrals." not in prompt
    assert "at most 5" in prompt
    usage = (await call(client, "GET", "/v1/usage/me", reader)).json()
    assert usage["quizzes"]["used_today"] == 1 and usage["card_suggestions"]["used_today"] == 0


# 2. Grading is done by code: score, per-question results, explanations and sources.
async def test_attempt_is_graded_by_code(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "Giải tích.pdf", [(4, "A derivative is the slope.")])
    ai.generate_script = [
        questions_json(
            ("Q1 derivative?", OPTIONS, 0, 1),
            ("Q2 derivative again?", OPTIONS, 0, 1),
            ("Q3 left blank?", OPTIONS, 0, 1),
        )
    ]
    quiz = (await create(client, reader, doc)).json()
    q1, q2, q3 = quiz["questions"]
    wrong = (correct(q2) + 1) % 4

    response = await call(
        client,
        "POST",
        f"/v1/quizzes/{quiz['id']}/attempts",
        reader,
        json={
            "answers": [
                {"question_id": q1["id"], "choice": correct(q1)},
                {"question_id": q2["id"], "choice": wrong},
                {"question_id": q3["id"], "choice": None},
            ]
        },
    )

    assert response.status_code == 201
    result = response.json()
    assert (result["score"], result["total"]) == (1, 3)
    assert [r["is_correct"] for r in result["results"]] == [True, False, False]
    second = result["results"][1]
    assert second["choice"] == wrong and second["correct_index"] == correct(q2)
    assert second["explanation"] == "Because Q2 derivative again?"
    assert second["source"] == {
        "document_id": str(doc),
        "document_name": "Giải tích.pdf",
        "page": 4,
    }
    assert len(ai.generate_calls) == 1  # grading never calls the AI

    listed = (
        await call(client, "GET", "/v1/quizzes", reader, params={"space_id": reader.space_id})
    ).json()["items"]
    assert [(q["attempt_count"], q["last_score"], q["question_count"]) for q in listed] == [
        (1, 1, 3)
    ]


# 3. Out-of-range choices and unknown question ids count as wrong.
async def test_invalid_choices_are_wrong(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "A.pdf", [(1, "x")])
    ai.generate_script = [questions_json(("Q?", OPTIONS, 0, 1))]
    quiz = (await create(client, reader, doc)).json()
    [q] = quiz["questions"]

    result = (
        await call(
            client,
            "POST",
            f"/v1/quizzes/{quiz['id']}/attempts",
            reader,
            json={
                "answers": [
                    {"question_id": q["id"], "choice": 7},
                    {"question_id": "00000000-0000-0000-0000-000000000000", "choice": 0},
                ]
            },
        )
    ).json()
    assert result["score"] == 0 and result["results"][0]["choice"] is None


# 4. Other users' quizzes are 404; deleting a quiz removes it.
async def test_ownership_and_delete(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    other = await new_reader(client, "other@example.com")
    doc = await seed_document(reader, "A.pdf", [(1, "x")])
    ai.generate_script = [questions_json(("Q?", OPTIONS, 0, 1))]
    quiz = (await create(client, reader, doc)).json()

    assert (await call(client, "GET", f"/v1/quizzes/{quiz['id']}", other)).status_code == 404
    response = await call(
        client, "POST", f"/v1/quizzes/{quiz['id']}/attempts", other, json={"answers": []}
    )
    assert response.status_code == 404
    assert (await call(client, "DELETE", f"/v1/quizzes/{quiz['id']}", other)).status_code == 404
    assert (await create(client, other, doc)).status_code == 404  # someone else's document
    assert (await call(client, "DELETE", f"/v1/quizzes/{quiz['id']}", reader)).status_code == 204
    assert (await call(client, "GET", f"/v1/quizzes/{quiz['id']}", reader)).status_code == 404


# 5. AI down or unusable output: 503, quota given back; quota used up: 429 without AI.
async def test_ai_failures_and_quota(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    doc = await seed_document(reader, "A.pdf", [(1, "x")])
    ai.generate_script = [AiQuotaExhaustedError(), json.dumps({"questions": [{"question": "bad"}]})]

    assert (await create(client, reader, doc)).status_code == 503
    assert (await create(client, reader, doc)).status_code == 503
    usage = (await call(client, "GET", "/v1/usage/me", reader)).json()
    assert usage["quizzes"]["used_today"] == 0

    key, _ = QuizQuota()._key(reader.user_id)
    await get_redis().set(key, settings.QUIZ_DAILY_LIMIT)
    calls = len(ai.generate_calls)
    response = await create(client, reader, doc)
    assert response.status_code == 429 and len(ai.generate_calls) == calls


# 6. Source checks and deleted documents.
async def test_sources(client: AsyncClient, ai: TopicProvider) -> None:
    reader = await new_reader(client)
    pending = await seed_document(reader, "P.pdf", [(1, "x")], status=PROCESSING)
    doc = await seed_document(reader, "A.pdf", [(1, "x")])

    assert (await create(client, reader, pending)).status_code == 409
    empty = await create(client, reader, doc, page_start=9)
    assert empty.status_code == 422 and empty.json()["code"] == "SOURCE_EMPTY"

    ai.generate_script = [questions_json(("Q?", OPTIONS, 0, 1))]
    quiz = (await create(client, reader, doc)).json()
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Document).where(Document.id == doc))
        await s.commit()
    [q] = quiz["questions"]
    result = (
        await call(
            client,
            "POST",
            f"/v1/quizzes/{quiz['id']}/attempts",
            reader,
            json={"answers": [{"question_id": q["id"], "choice": 0}]},
        )
    ).json()
    assert result["results"][0]["source"]["document_id"] is None
    assert result["results"][0]["source"]["document_name"] == "A.pdf"
