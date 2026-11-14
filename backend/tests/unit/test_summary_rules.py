"""F12 pure rules: finding chapters and reading AI summary output."""

from __future__ import annotations

import json

from app.modules.study.source_material import Passage
from app.modules.study.summaries.prompts import parse_points
from app.modules.study.summaries.sections import SectionDraft, find_sections, page_parts


def test_chapters_follow_headings_with_a_leading_part() -> None:
    pages = [
        "Lời nói đầu\n\nGiới thiệu môn học.",
        "Chương 1. Giới hạn\n\nGiới hạn mô tả...",
        "Tiếp chương 1.",
        "Chương 2. Đạo hàm\n\nĐạo hàm là...",
    ]
    assert find_sections(pages, pages_per_part=10, max_sections=40) == [
        SectionDraft(None, 1, 1),
        SectionDraft("Chương 1. Giới hạn", 2, 3),
        SectionDraft("Chương 2. Đạo hàm", 4, 4),
    ]


def test_two_headings_on_one_page() -> None:
    pages = ["Chapter 1 Intro\n\nText.\n\nChapter 2 More\n\nText.", "Rest."]
    sections = find_sections(pages, pages_per_part=10, max_sections=40)
    assert [(s.title, s.page_start, s.page_end) for s in sections] == [
        ("Chapter 1 Intro", 1, 1),
        ("Chapter 2 More", 1, 2),
    ]


def test_no_headings_or_too_many_falls_back_to_page_ranges() -> None:
    plain = ["Text."] * 23
    assert find_sections(plain, pages_per_part=10, max_sections=40) == page_parts(23, 10)
    assert [(p.page_start, p.page_end) for p in page_parts(23, 10)] == [(1, 10), (11, 20), (21, 23)]
    many = [f"Mục {i}\n\nText." for i in range(1, 6)]
    assert find_sections(many, pages_per_part=2, max_sections=3) == page_parts(5, 2)


def test_parse_points_maps_sources_to_pages() -> None:
    sources = [Passage(None, "A.pdf", 2, 2, "x"), Passage(None, "A.pdf", 3, 4, "y")]
    raw = json.dumps(
        {
            "points": [
                {"text": " Ý một ", "source": 2},
                {"text": "Ý hai", "source": 9},
                {"text": "   "},
                {"text": 5},
            ]
        }
    )
    points = parse_points(raw, sources)
    assert [(p.text, p.page) for p in points] == [("Ý một", 3), ("Ý hai", None)]
    assert parse_points("nope", sources) == []
