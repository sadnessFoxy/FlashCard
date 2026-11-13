"""Pure logic for F5: chunking, PDF checks, file names, state machine, Gemini errors, gateway."""

from __future__ import annotations

import pytest

from app.core.exceptions import (
    AiCircuitOpenError,
    AiQuotaExhaustedError,
    AiRateLimitedError,
    AiTemporarilyUnavailableError,
    ContextTooLongError,
)
from app.integrations.llm_gateway.circuit_breaker import CircuitBreaker
from app.integrations.llm_gateway.gateway import LLMGateway
from app.modules.ai.providers.fake import FakeProvider
from app.modules.ai.providers.gemini_errors import classify_gemini_error
from app.modules.documents import states
from app.modules.documents.chunking import chunk_pages
from app.modules.documents.filenames import sanitize_filename
from app.modules.documents.pdf import NotAPdfError, inspect_pdf, looks_scanned
from tests.fixtures.pdfs import make_pdf

# ------------------------------------------------------------- chunking


def chunk(pages: list[str], target: int = 200, overlap: int = 30, max_chars: int = 400):  # type: ignore[no-untyped-def]
    return chunk_pages(pages, target_chars=target, overlap_chars=overlap, max_chars=max_chars)


def test_chunks_respect_target_and_track_pages() -> None:
    pages = ["\n\n".join(f"Page one paragraph {i} " + "x" * 60 for i in range(4)), "Page two text."]

    chunks = chunk(pages)

    assert len(chunks) >= 2
    assert all(len(c.content) <= 400 for c in chunks)
    assert chunks[0].page_start == 1
    assert chunks[-1].page_end == 2
    assert all(c.page_start <= c.page_end for c in chunks)


def test_consecutive_chunks_overlap() -> None:
    pages = ["\n\n".join(f"word{i} " * 20 for i in range(6))]

    chunks = chunk(pages, target=150, overlap=40)

    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        tail = prev.content.split()[-1]
        assert tail in nxt.content


def test_long_paragraph_is_split_under_max() -> None:
    sentence = "This is a sentence. "
    chunks = chunk([sentence * 200], target=300, overlap=50, max_chars=500)

    assert len(chunks) > 1
    assert all(len(c.content) <= 500 for c in chunks)


def test_unbreakable_text_is_hard_cut() -> None:
    chunks = chunk(["x" * 2000], target=300, overlap=0, max_chars=500)

    assert all(len(c.content) <= 500 for c in chunks)
    assert sum(len(c.content) for c in chunks) >= 2000


def test_empty_pages_give_no_chunks() -> None:
    assert chunk(["", "   \n  "]) == []


def test_vietnamese_text_is_kept_nfc() -> None:
    decomposed = "Đạo hàm"  # NFD input
    [only] = chunk([decomposed])
    assert only.content == "Đạo hàm"


def test_headings_start_new_chunks_without_overlap() -> None:
    pages = [
        "Chương 1. Giới hạn\nGiới hạn mô tả giá trị hàm số tiến tới.\n"
        "Chương 2. Đạo hàm\nĐạo hàm là tốc độ thay đổi tức thời."
    ]

    chunks = chunk(pages, target=1000, overlap=50)

    assert [c.content.split(".")[0] for c in chunks] == ["Chương 1", "Chương 2"]
    assert "Giới hạn" not in chunks[1].content  # no overlap across a heading


def test_new_page_starts_new_chunk_so_citations_are_exact() -> None:
    pages = ["A" * 300 + ".", "Second page text about derivatives."]

    chunks = chunk(pages, target=1000, overlap=50)

    assert [(c.page_start, c.page_end) for c in chunks] == [(1, 1), (2, 2)]


def test_tiny_page_tail_is_merged_with_next_page() -> None:
    pages = ["Short.", "Next page continues the same section."]

    [only] = chunk(pages, target=1000, overlap=50)

    assert (only.page_start, only.page_end) == (1, 2)


def test_lines_ending_with_punctuation_split_paragraphs() -> None:
    page = "\n".join(f"Sentence number {i} ends here." for i in range(40))

    chunks = chunk([page], target=300, overlap=40, max_chars=600)

    assert len(chunks) > 1 and all(len(c.content) <= 600 for c in chunks)
    assert all(c.content.endswith(".") for c in chunks)


# ------------------------------------------------------------------ pdf


def test_inspect_pdf_rejects_non_pdf() -> None:
    with pytest.raises(NotAPdfError):
        inspect_pdf(b"PK\x03\x04 this is a zip")
    with pytest.raises(NotAPdfError):
        inspect_pdf(b"%PDF-1.4 but then garbage")


def test_inspect_pdf_counts_pages() -> None:
    assert inspect_pdf(make_pdf(["a", "b", "c"])).page_count == 3


def test_scan_detection() -> None:
    assert looks_scanned(["", " ", "12"], min_chars_per_page=20)
    assert not looks_scanned(["x" * 50, ""], min_chars_per_page=20)
    assert looks_scanned([], min_chars_per_page=20)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Giáo trình.pdf", "Giáo trình.pdf"),
        ("C:\\fakepath\\notes.pdf", "notes.pdf"),
        ("../../etc/passwd", "passwd"),
        ("a\x00b\x1fc.pdf", "abc.pdf"),
        ("", "document.pdf"),
        (None, "document.pdf"),
        ("x" * 300 + ".pdf", "x" * 255),
    ],
)
def test_sanitize_filename(raw: str | None, expected: str) -> None:
    assert sanitize_filename(raw) == expected


# ------------------------------------------------------- state machine


@pytest.mark.parametrize(
    ("source", "target", "allowed"),
    [
        ("QUEUED", "PROCESSING", True),
        ("PROCESSING", "READY", True),
        ("PROCESSING", "PAUSED_QUOTA", True),
        ("PROCESSING", "QUEUED", True),
        ("PAUSED_QUOTA", "QUEUED", True),
        ("READY", "PROCESSING", False),
        ("DELETING", "READY", False),
        ("FAILED", "READY", False),
        ("UPLOADED", "READY", False),
    ],
)
def test_transitions(source: str, target: str, allowed: bool) -> None:
    assert states.can_transition(source, target) is allowed


def test_everything_can_be_deleted_except_deleting() -> None:
    assert states.sources_for("DELETING") == frozenset(states.ALL_STATUSES) - {"DELETING"}


# ------------------------------------------------------- gemini errors


def _err(status: str, message: str = "", details: list[dict] | None = None) -> dict:  # type: ignore[type-arg]
    return {"error": {"status": status, "message": message, "details": details or []}}


def test_per_minute_429_is_rate_limited_with_retry_delay() -> None:
    body = _err(
        "RESOURCE_EXHAUSTED",
        "Quota exceeded",
        [
            {
                "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                "violations": [{"quotaId": "EmbedContentRequestsPerMinutePerProjectPerModel"}],
            },
            {"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "17s"},
        ],
    )
    exc = classify_gemini_error(429, body)
    assert isinstance(exc, AiRateLimitedError)
    assert exc.retry_after_seconds == 17


def test_daily_429_is_quota_exhausted() -> None:
    body = _err(
        "RESOURCE_EXHAUSTED",
        details=[
            {
                "@type": "type.googleapis.com/google.rpc.QuotaFailure",
                "violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}],
            }
        ],
    )
    assert isinstance(classify_gemini_error(429, body), AiQuotaExhaustedError)


@pytest.mark.parametrize(
    ("status_code", "body", "expected"),
    [
        (
            429,
            _err("RESOURCE_EXHAUSTED", "Please check your plan and billing details"),
            AiQuotaExhaustedError,
        ),
        (403, _err("PERMISSION_DENIED"), AiQuotaExhaustedError),
        (400, _err("INVALID_ARGUMENT", "API key not valid"), AiQuotaExhaustedError),
        (400, _err("INVALID_ARGUMENT", "input is too long"), ContextTooLongError),
        (503, _err("UNAVAILABLE"), AiTemporarilyUnavailableError),
        (500, "not json", AiTemporarilyUnavailableError),
    ],
)
def test_other_gemini_errors(status_code: int, body: object, expected: type) -> None:
    assert type(classify_gemini_error(status_code, body)) is expected


# ------------------------------------------------------------- gateway


async def _no_record(**_: object) -> None:
    return None


def _gateway(provider: FakeProvider, sleeps: list[float]) -> LLMGateway:
    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)

    return LLMGateway(
        provider,
        breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=60),
        sleep=sleep,
        recorder=_no_record,
    )


async def test_gateway_waits_out_rate_limits() -> None:
    provider = FakeProvider()
    provider.embed_script = [AiRateLimitedError(retry_after_seconds=7), None]
    sleeps: list[float] = []

    vectors = await _gateway(provider, sleeps).embed(["a"])

    assert len(vectors) == 1 and sleeps == [7]


async def test_gateway_caps_rate_limit_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "AI_RATE_LIMIT_MAX_WAIT_SECONDS", 10)
    provider = FakeProvider()
    provider.embed_script = [AiRateLimitedError(retry_after_seconds=500), None]
    sleeps: list[float] = []

    await _gateway(provider, sleeps).embed(["a"])

    assert sleeps == [10]


async def test_gateway_never_retries_quota_and_trips_breaker() -> None:
    provider = FakeProvider()
    provider.embed_script = [AiQuotaExhaustedError()]
    gateway = _gateway(provider, [])

    with pytest.raises(AiQuotaExhaustedError):
        await gateway.embed(["a"])
    with pytest.raises(AiCircuitOpenError):
        await gateway.embed(["a"])
    assert provider.embed_calls == []


async def test_gateway_retries_transient_errors_then_gives_up() -> None:
    provider = FakeProvider()
    provider.embed_script = [AiTemporarilyUnavailableError()] * 3
    sleeps: list[float] = []

    with pytest.raises(AiTemporarilyUnavailableError):
        await _gateway(provider, sleeps).embed(["a"])

    assert sleeps == [1.0, 2.0]


async def test_gateway_recovers_after_one_transient_error() -> None:
    provider = FakeProvider()
    provider.embed_script = [AiTemporarilyUnavailableError(), None]

    assert len(await _gateway(provider, []).embed(["a", "b"])) == 2
