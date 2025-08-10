# services/metadata.py
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol

# Your concrete repo
from lib.repositories.metadata_repository import MetadataRepository


# --- Dependency Interface (what this service needs) ---------------------------
class MetadataRepo(Protocol):
    def update_next(self, _id: str, next_value: str) -> tuple[int, int]:
        """Return (matched_count, modified_count)."""
        ...

    def all_sorted_desc(self) -> Iterable[dict]:
        """Yield metadata docs in reverse chronological order."""
        ...


# --- Production adapter for your existing repo -------------------------------
class _DefaultMetadataRepoAdapter(MetadataRepo):
    def __init__(self, repo: MetadataRepository | None = None) -> None:
        self._repo = repo or MetadataRepository()

    def update_next(self, _id: str, next_value: int) -> tuple[int, int]:
        res = self._repo.update_metadata({"_id": _id}, {"$set": {"next": next_value}})
        # pymongo UpdateResult exposes matched_count/modified_count
        return getattr(res, "matched_count", 0), getattr(res, "modified_count", 0)

    def all_sorted_desc(self) -> Iterable[dict]:
        # Use existing API to stream all docs newest-first by _id
        # If you later store a proper date field + index, sort by that instead.
        cursor = self._repo.get_metadata({}, sorting=[("_id", -1)])
        return cursor


# --- Pure helpers ------------------------------------------------------------
def _parse_id_parts(sample_id: str) -> tuple[int, datetime] | None:
    """
    Expect IDs like: '<prefix>-YYYY-MM-DD' e.g. '2-2025-06-19'.
    Returns (prefix_int, date_obj) or None if malformed.
    """
    parts = sample_id.split("-")
    if len(parts) < 4:
        return None
    try:
        prefix = int(parts[0])
        date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return prefix, dt
    except Exception:
        return None


# --- Service API -------------------------------------------------------------
def update_next_in_previous_doc(to_update: str, next_value: str, repo: MetadataRepo | None = None) -> bool:
    """
    Update the 'next' field of the metadata document with _id=to_update.
    Returns True iff an existing doc was modified.
    """
    repo = repo or _DefaultMetadataRepoAdapter()
    matched, modified = repo.update_next(to_update, next_value)
    return matched > 0 and modified > 0


def find_last_sample(repo: MetadataRepo | None = None) -> str | None:
    """
    Return the latest sample _id, ordering by (date, then prefix when same day).
    """
    repo = repo or _DefaultMetadataRepoAdapter()

    latest_id: str | None = None
    latest_date: datetime | None = None
    latest_prefix: int | None = None

    for doc in repo.all_sorted_desc():
        raw_id = doc.get("_id")
        if not isinstance(raw_id, str):
            continue

        parsed = _parse_id_parts(raw_id)
        if not parsed:
            continue

        prefix, doc_date = parsed

        if (
            latest_date is None
            or doc_date > latest_date
            or (doc_date == latest_date and (latest_prefix is None or prefix > latest_prefix))
        ):
            latest_id = raw_id
            latest_date = doc_date
            latest_prefix = prefix

    return latest_id


__all__ = ["MetadataRepo", "update_next_in_previous_doc", "find_last_sample"]
