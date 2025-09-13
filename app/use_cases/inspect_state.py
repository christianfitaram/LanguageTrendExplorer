from __future__ import annotations

import os
from typing import Any, Dict

from pymongo import MongoClient
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "trending_words")

repo_metadata = MetadataRepository()
repo_articles = ArticlesRepository()
repo_clean_articles = CleanArticlesRepository()


def inspect_state(limit_samples: int = 5) -> Dict[str, Any]:

    """Inspect the current state of the application, including metadata, article counts, and backlog.
    :param limit_samples: Number of latest samples to inspect.
    :return: A dictionary containing the latest metadata, per-sample article counts, backlog counts, and top sources.
    """

    # latest N samples (you store per-sample metadata under _id = sample) :contentReference[oaicite:5]{index=5}
    latest_meta = list(
        repo_metadata.get_metadata_broad({}, {"_id": 1, "topic_distribution": 1, "sentiment_distribution": 1,
                                              "articles_processed": 1, "raw_total_words": 1, "distinct_words": 1,
                                              "gathering_sample_startedAt": 1, "gathering_sample_finishedAt": 1})
        .sort([("_id", -1)]).limit(limit_samples))
    sample_ids = [m["_id"] for m in latest_meta]

    # counts per sample
    per_sample_counts = []
    for sid in sample_ids:
        a_cnt = repo_articles.count_articles({"sample": sid})
        c_cnt = repo_clean_articles.count_articles({"sample": sid})
        per_sample_counts.append({"sample": sid, "articles": a_cnt, "clean_articles": c_cnt})

    # backlog (not yet processed in cleaner or analyzer)
    backlog_clean = repo_articles.count_articles({"isCleaned": {"$ne": True}})
    backlog_processed = repo_clean_articles.count_articles({"isProcessed": {"$ne": True}})

    # sources: quick health signal
    top_sources = list(repo_articles.aggregate_articles([
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]))

    return {
        "latest_meta": latest_meta,
        # includes topic/sentiment distributions written by gather step :contentReference[oaicite:6]{index=6}
        "per_sample_counts": per_sample_counts,
        "backlog": {"to_clean": backlog_clean, "to_mark_processed": backlog_processed},
        "top_sources": top_sources
    }
