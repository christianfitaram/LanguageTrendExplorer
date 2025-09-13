from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

# Ensure the MongoDB connection is established
from lib.repositories.link_pool_repository import LinkPoolRepository
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.clean_articles_repository import CleanArticlesRepository

repo_link_pool = LinkPoolRepository()
repo_articles = ArticlesRepository()
repo_clean_articles = CleanArticlesRepository()


def prune_stale(days: int = 7) -> dict:
    """Prune stale entries from the link pool, articles, and clean articles collections."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # 1) link_pool: keep URLs that landed in a sample; drop old, never-used entries Your gate treats a URL as
    # processed if doc.has is_articles_processed or in_sample. :contentReference[oaicite:4]{index=4}
    res1 = repo_link_pool.delete_links({
        "in_sample": {"$ne": True},
        "is_articles_processed": {"$ne": True},
        "createdAt": {"$lt": cutoff}
    })

    # 2) articles: remove orphan rows with no text (failed extraction) older than window
    res2 = repo_articles.delete_articles({
        "$or": [{"text": {"$exists": False}}, {"text": ""}],
        "scraped_at": {"$lt": cutoff}
    })

    # 3) clean_articles: drop rows already marked processed long ago (safe to recompute later)
    res3 = repo_clean_articles.delete_articles({
        "isProcessed": True,
        "scraped_at": {"$lt": cutoff}
    })

    return {
        "link_pool_deleted": res1,
        "articles_deleted": res2,
        "clean_deleted": res3,
        "cutoff": cutoff.isoformat(),
    }
