# adapters/link_pool_gate.py
from typing import Protocol, Optional, Dict, Any


class LinkPoolRepo(Protocol):
    def find_one_by_url(self, url: str, *, projection: dict | None = None) -> Optional[Dict[str, Any]]: ...
    def ensure_tracked(self, url: str): ...
    def mark_processed(self, url: str, sample_id: str) -> int: ...

class LinkPoolGate:
    def __init__(self, repo: LinkPoolRepo) -> None:
        self.repo = repo

    def is_processed(self, url: str) -> bool:
        doc = self.repo.find_one_by_url(url, projection={"is_articles_processed": 1, "in_sample": 1})
        return bool(doc and (doc.get("is_articles_processed") or doc.get("in_sample")))

    def ensure_tracked(self, url: str) -> None:
        self.repo.ensure_tracked(url)

    def mark_processed(self, url: str, sample_id: str) -> None:
        self.repo.mark_processed(url, sample_id)
