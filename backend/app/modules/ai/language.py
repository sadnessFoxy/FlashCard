"""Tell the app's two languages apart (vi, en) so prompts can name the answer language."""

from __future__ import annotations

import re

# Letters only Vietnamese uses among the two languages.
_VIETNAMESE = re.compile(
    r"[ăâđêôơưàáạảãằắặẳẵầấậẩẫèéẹẻẽềếệểễìíịỉĩòóọỏõồốộổỗờớợởỡùúụủũừứựửữỳýỵỷỹ]",
    re.IGNORECASE,
)


def detect_language(text: str) -> str:
    """'Vietnamese' or 'English', as written in prompts."""
    return "Vietnamese" if _VIETNAMESE.search(text) else "English"
