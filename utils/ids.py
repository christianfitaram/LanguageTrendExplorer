# ids.py

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional


def date_key(dt: Optional[datetime] = None) -> str:
    """
    Returns YYYY-MM-DD in UTC (or provided dt’s date in UTC).
    """
    dt = dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def compute_sample_id(batch_number: int | None = None, dt: Optional[datetime] = None) -> str:
    """
    Returns a stable sample_id like: "2-2025-08-18"
    If batch_number is None, defaults to 1.
    """
    b = batch_number or 1
    return f"{b}-{date_key(dt)}"
