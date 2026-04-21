"""Text normalization for the support intent classifier."""
from __future__ import annotations

import re
import unicodedata

_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase + NFC-normalize + collapse whitespace.

    Accents are intentionally preserved — they carry meaning in DE/ES/FR/IT.
    Char n-grams handle morphology robustly, so aggressive stripping hurts
    more than it helps.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = _WS_RE.sub(" ", text).strip()
    return text
