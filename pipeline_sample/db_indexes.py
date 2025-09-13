from __future__ import annotations
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from lib.repositories.link_pool_repository import LinkPoolRepository
from lib.repositories.daily_trends_repository import DailyTrendsRepository
from lib.repositories.trend_threads_repository import TrendThreadsRepository

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "trending_words")

repo_articles = ArticlesRepository()
repo_clean_articles = CleanArticlesRepository()
repo_metadata = MetadataRepository()
repo_link_pool = LinkPoolRepository()
repo_daily_trends = DailyTrendsRepository()
repo_trend_threads = TrendThreadsRepository()


def ensure_indexes() -> None:
    """
    Ensure all necessary indexes are created for the MongoDB collections used in the application.
    """

    # --- articles ---
    repo_articles.create_index([("sample", ASCENDING)])
    repo_articles.create_index([("url", ASCENDING)], unique=False)
    repo_articles.create_index([("isCleaned", ASCENDING), ("sample", ASCENDING)])

    # --- clean_articles ---
    repo_clean_articles.create_index([("sample", ASCENDING), ("isProcessed", ASCENDING)])
    repo_clean_articles.create_index([("url", ASCENDING)])

    # --- metadata ---
    repo_metadata.create_index([("_id", DESCENDING)], unique=True)  # sample_id as PK
    repo_metadata.create_index([("gathering_sample_startedAt", DESCENDING)])
    repo_metadata.create_index([("gathering_sample_finishedAt", DESCENDING)])

    # --- link_pool (flags consulted by your gate) ---
    # gate checks is_articles_processed OR in_sample; index them for quick lookups
    repo_link_pool.create_index([("url", ASCENDING)], unique=True)
    repo_link_pool.create_index([("is_articles_processed", ASCENDING)])
    repo_link_pool.create_index([("in_sample", ASCENDING)])

    # --- trends (Phase 4) ---
    repo_trend_threads.create_index([("date", ASCENDING), ("thread_id", ASCENDING)], unique=True)
    repo_daily_trends.create_index([("date", DESCENDING), ("trend_score", DESCENDING)])
    repo_daily_trends.create_index([("thread_id", ASCENDING), ("date", DESCENDING)])

    print("✅ Indexes ensured for articles, clean_articles, metadata, link_pool, trend_threads, daily_trends.")
