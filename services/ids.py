# services/ids.py
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from services.batches import get_next_batch_number, ArticlesRepo


def _to_iso_date(d: Optional[date] = None) -> str:
    """Return YYYY-MM-DD; defaults to today's UTC date."""
    if d is None:
        d = datetime.now(timezone.utc).date()
    return d.strftime("%Y-%m-%d")


def generate_id(repo: Optional[ArticlesRepo] = None, for_date: Optional[date] = None) -> str:
    """
    Build an ID like '<batch>-YYYY-MM-DD' using the next batch number for the given day.

    Args:
        repo: Articles repository (DI). If None, uses the default ArticlesRepository().
        for_date: Generate the ID for this date instead of today (UTC).

    Returns:
        str: e.g. '3-2025-08-10'
    """
    # Important: get_next_batch_number uses "today" internally.
    # If you pass a date different from today, we compute the batch by temporarily
    # monkey-patching the date string computation. To avoid side effects, we just
    # re-implement the needed behavior here when for_date is provided.

    if for_date is None:
        batch = get_next_batch_number(repo)
        today_str = _to_iso_date()
        return f"{batch}-{today_str}"

    # When for_date is specified, we need the next batch *for that date*.
    # We'll query the repo directly to avoid changing get_next_batch_number's internals.
    if repo is None:
        # Lazy import to avoid circular import of the concrete repo at import time.
        from lib.repositories.articles_repository import ArticlesRepository
        repo = ArticlesRepository()  # type: ignore[assignment]

    target_str = _to_iso_date(for_date)
    samples = repo.get_distinct_samples(target_str)

    # Extract numeric batch prefixes from samples like '2-YYYY-MM-DD'
    batches = []
    for s in samples:
        parts = s.split("-")
        if len(parts) >= 4:
            try:
                batches.append(int(parts[0]))
            except ValueError:
                pass

    next_batch = (max(batches) + 1) if batches else 1
    return f"{next_batch}-{target_str}"


__all__ = ["generate_id"]
