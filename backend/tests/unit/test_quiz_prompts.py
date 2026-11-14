"""F11 pure rules: checking and shuffling AI quiz output."""

from __future__ import annotations

import json
import random

from app.modules.study.quizzes.prompts import (
    OPTION_COUNT,
    DraftQuestion,
    build_request,
    parse_questions,
)
from app.modules.study.source_material import Passage

GOOD = {
    "question": "Q?",
    "options": ["a", "b", "c", "d"],
    "answer": 2,
    "explanation": "e",
    "source": 1,
}


def parse(*items: object, limit: int = 10, seed: int = 1) -> list[DraftQuestion]:
    return parse_questions(json.dumps({"questions": list(items)}), 2, limit, random.Random(seed))


def test_correct_option_survives_the_shuffle() -> None:
    for seed in range(20):
        [q] = parse(GOOD, seed=seed)
        assert q.options[q.correct_index] == "c"
        assert sorted(q.options) == ["a", "b", "c", "d"]


def test_shuffle_spreads_the_correct_slot() -> None:
    slots = {parse(GOOD, seed=s)[0].correct_index for s in range(40)}
    assert len(slots) > 1


def test_malformed_questions_are_dropped() -> None:
    bad = [
        {**GOOD, "options": ["a", "b", "c"]},  # three options
        {**GOOD, "options": ["a", "a", "b", "c"]},  # duplicates
        {**GOOD, "answer": 4},  # answer out of range
        {**GOOD, "question": "  "},  # empty question
        "not a question",
    ]
    assert parse(*bad) == []
    assert parse_questions("not json", 1, 5) == []


def test_duplicates_limit_and_sources() -> None:
    items = [
        GOOD,
        {**GOOD, "question": "q?"},
        {**GOOD, "question": "Q2", "source": 9},
        {**GOOD, "question": "Q3"},
    ]
    questions = parse(*items, limit=2)
    assert [q.prompt for q in questions] == ["Q?", "Q2"]
    assert questions[1].source_index is None
    assert all(len(q.options) == OPTION_COUNT for q in questions)


def test_request_names_language_and_count() -> None:
    request = build_request([Passage(None, "A.pdf", 1, 1, "Đạo hàm là hệ số góc")], 7)
    assert "at most 7 questions in Vietnamese" in request
