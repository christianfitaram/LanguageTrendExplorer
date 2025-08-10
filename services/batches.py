# services/batches.py
from __future__ import annotations

from datetime import datetime, UTC
from typing import List, Protocol, Optional

# Default concrete repo (only used if caller doesn't inject one)
from lib.repositories.articles_repository import ArticlesRepository


class ArticlesRepo(Protocol):
    """Minimal interface needed by this service."""
    def get_distinct_samples(self, today_str: str) -> List[str]: ...


def _extract_batch_numbers(samples: List[str]) -> List[int]:
    """
    Samples look like: "<batch>-YYYY-MM-DD" (e.g., "2-2025-08-10").
    We extract the leading integer <batch>. Malformed entries are ignored.
    """
    batches: List[int] = []
    for s in samples:
        parts = s.split("-")
        if len(parts) >= 4:
            try:
                batches.append(int(parts[0]))
            except ValueError:
                # ignore malformed batch prefix
                pass
    return batches


def get_next_batch_number(repo: Optional[ArticlesRepo] = None) -> int:
    """
    Compute the next batch number for *today* by scanning existing samples.

    Priority:
      - Use injected repo (for tests / custom wiring)
      - Fallback to the default ArticlesRepository

    Returns:
      Next integer batch number (>= 1).
    """
    if repo is None:
        repo = ArticlesRepository()

    today_str = datetime.now(UTC).date().strftime("%Y-%m-%d")
    samples = repo.get_distinct_samples(today_str)

    batches = _extract_batch_numbers(samples)
    return (max(batches) + 1) if batches else 1


__all__ = ["ArticlesRepo", "get_next_batch_number"]
