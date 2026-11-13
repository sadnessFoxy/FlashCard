"""Build small PDFs in memory for tests (no binary fixtures in the repo)."""

from __future__ import annotations

import io

from pypdf import PdfWriter


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages: list[str]) -> bytes:
    """A valid PDF whose pages contain the given ASCII text (paragraphs split by blank lines)."""
    objects: list[bytes] = []
    n = len(pages)
    page_ids = [4 + 2 * i for i in range(n)]
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i, text in enumerate(pages):
        lines = []
        for line in text.split("\n"):
            lines.append(f"({_escape(line)}) Tj 0 -14 Td")
        stream = ("BT /F1 11 Tf 50 780 Td " + " ".join(lines) + " ET").encode("latin-1")
        content_id = page_ids[i] + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode()
        )
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def make_blank_pdf(pages: int) -> bytes:
    """Pages without any text layer, like a scan."""
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def make_encrypted_pdf() -> bytes:
    writer = PdfWriter(clone_from=io.BytesIO(make_pdf(["secret"])))
    writer.encrypt(user_password="pw", owner_password="owner")
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def lorem(paragraphs: int, words: int = 60, seed: str = "") -> str:
    """Deterministic filler text with distinct paragraphs."""
    vocab = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu".split()
    out = []
    for p in range(paragraphs):
        out.append(" ".join(f"{vocab[(p + w) % len(vocab)]}{seed}{p}" for w in range(words)))
    return "\n\n".join(out)
