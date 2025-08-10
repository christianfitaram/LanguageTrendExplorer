from __future__ import annotations

from typing import Protocol, Optional

from lib.repositories.link_pool_repository import LinkPoolRepository


class LinkPoolRepo(Protocol):
    """Minimal interface needed by this service."""

    def is_link_successfully_processed(self, url: str) -> bool: ...


def is_urls_processed_already(url: str, repo: Optional[LinkPoolRepository] = None) -> bool:
    """
    Check if a URL have been already processed
    """
    if repo is None:
        repo = LinkPoolRepository()

    is_it = repo.is_link_successfully_processed(url)

    if is_it:
        print(f"{url} it has been processed already. Skipping ")
        return True
    else:
        return False


__all__ = ["LinkPoolRepo", "is_urls_processed_already"]
