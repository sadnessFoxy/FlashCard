"""
SM-2 scheduling as a pure function (docs/specs/f10-reviews.md section 6).

The app offers four grades mapped to SM-2 quality: again=1, hard=3, good=4, easy=5.
- quality < 3 (again): start over; the card comes back in RELEARN_MINUTES, ease drops.
- otherwise: repetitions + 1; interval 1 day, then 6 days, then previous interval * ease.
  "easy" gets an extra EASY_BONUS on the interval.
- ease' = ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)), never below MIN_EASE.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

Grade = Literal["again", "hard", "good", "easy"]

QUALITY: dict[str, int] = {"again": 1, "hard": 3, "good": 4, "easy": 5}
MIN_EASE = 1.3
RELEARN_MINUTES = 10
EASY_BONUS = 1.3
FIRST_INTERVAL_DAYS = 1
SECOND_INTERVAL_DAYS = 6


@dataclass(frozen=True)
class Schedule:
    ease_factor: float
    interval_days: int
    repetitions: int
    due_at: datetime


def next_ease(ease: float, quality: int) -> float:
    miss = 5 - quality
    return max(MIN_EASE, round(ease + (0.1 - miss * (0.08 + miss * 0.02)), 4))


def schedule(current: Schedule, grade: Grade, reviewed_at: datetime) -> Schedule:
    quality = QUALITY[grade]
    ease = next_ease(current.ease_factor, quality)
    if quality < 3:
        return Schedule(ease, 0, 0, reviewed_at + timedelta(minutes=RELEARN_MINUTES))

    repetitions = current.repetitions + 1
    if repetitions == 1:
        interval = FIRST_INTERVAL_DAYS
    elif repetitions == 2:
        interval = SECOND_INTERVAL_DAYS
    else:
        interval = round(max(current.interval_days, 1) * ease)
    if grade == "easy":
        interval = round(interval * EASY_BONUS)
    interval = max(1, interval)
    return Schedule(ease, interval, repetitions, reviewed_at + timedelta(days=interval))
