# adapters/scrapers.py
from __future__ import annotations
from typing import Iterable, Dict, Any, Callable


class FunctionScraper:
    """Adapts a plain generator function into the Scraper Protocol."""

    def __init__(self, fn: Callable[[], Iterable[Dict[str, Any]]]) -> None:
        self.fn = fn

    def stream(self) -> Iterable[Dict[str, Any]]:
        yield from self.fn()
