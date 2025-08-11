# utils/safety.py
from __future__ import annotations
from typing import Any, Iterable

def coerce_text(x: Any) -> str:
    """
    Normalize possibly-None, lists, dicts, bytes to a clean str.
    Never returns None.
    """
    if x is None:
        return ""
    if isinstance(x, bytes):
        try:
            return x.decode("utf-8", errors="ignore").strip()
        except Exception:
            return ""
    if isinstance(x, (list, tuple)):
        return "\n".join([coerce_text(y) for y in x]).strip()
    if isinstance(x, dict):
        # Common extractor shape: {"text": "...", "title": "..."}
        if "text" in x and isinstance(x["text"], (str, bytes, list, tuple)):
            return coerce_text(x["text"])
        return str(x).strip()
    return str(x).strip()

def safe_len(x: Any) -> int:
    """
    len() that returns 0 for non-sized/None values instead of exploding.
    """
    try:
        return len(x)  # type: ignore[arg-type]
    except Exception:
        return 0

def is_non_empty_text(x: Any, min_chars: int = 1) -> bool:
    s = coerce_text(x)
    return len(s) >= min_chars

def join_paragraphs(chunks: Iterable[Any]) -> str:
    return "\n".join(coerce_text(c) for c in chunks if coerce_text(c)).strip()
