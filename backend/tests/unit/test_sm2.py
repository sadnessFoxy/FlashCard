"""SM-2 rules (docs/specs/f10-reviews.md section 6; docs/TESTING.md)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.modules.study.reviews.sm2 import MIN_EASE, Schedule, next_ease, schedule

NOW = datetime(2026, 11, 13, 8, 0, tzinfo=UTC)
NEW = Schedule(ease_factor=2.5, interval_days=0, repetitions=0, due_at=NOW)


def test_first_good_reviews_follow_1_then_6_days_then_ease() -> None:
    first = schedule(NEW, "good", NOW)
    assert (first.repetitions, first.interval_days, first.due_at) == (1, 1, NOW + timedelta(days=1))
    second = schedule(first, "good", NOW)
    assert (second.repetitions, second.interval_days) == (2, 6)
    third = schedule(second, "good", NOW)
    assert third.interval_days == round(6 * third.ease_factor) == 15


def test_again_resets_and_comes_back_soon() -> None:
    learned = Schedule(2.5, 15, 3, NOW)
    lapsed = schedule(learned, "again", NOW)
    assert (lapsed.repetitions, lapsed.interval_days) == (0, 0)
    assert lapsed.due_at == NOW + timedelta(minutes=10)
    assert lapsed.ease_factor == pytest.approx(1.96)


@pytest.mark.parametrize(("quality", "expected"), [(5, 2.6), (4, 2.5), (3, 2.36), (1, 1.96)])
def test_ease_formula(quality: int, expected: float) -> None:
    assert next_ease(2.5, quality) == pytest.approx(expected)


def test_ease_never_below_minimum() -> None:
    assert next_ease(MIN_EASE, 1) == MIN_EASE


def test_easy_gets_a_bonus_and_hard_lowers_ease() -> None:
    easy = schedule(NEW, "easy", NOW)
    assert easy.interval_days == 1  # round(1 * 1.3)
    assert schedule(Schedule(2.5, 6, 2, NOW), "easy", NOW).interval_days == round(
        round(6 * 2.6) * 1.3
    )
    hard = schedule(NEW, "hard", NOW)
    assert hard.repetitions == 1 and hard.ease_factor == pytest.approx(2.36)
