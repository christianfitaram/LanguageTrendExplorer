# pipeline_sample/exec_cleaner.py

"""CLI entry point for cleaning articles (called by Typer)."""
from __future__ import annotations

from typing import Optional

from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from lib.repositories.summaries_repository import SummariesRepository
from services.articles import ArticlesService
from utils.validation import is_valid_sample


def clean_articles(sample_temp: Optional[str] = None) -> str:
    """
    Clean raw articles for a given sample.
    - If sample_id is None, prompt interactively.
    """
    if sample_temp is None:
        sample_temp = input("Enter the sample string (e.g. '1-2025-04-12'): ")
        while not is_valid_sample(sample_temp):
            sample_temp = input("Incorrect format (e.g. '1-2025-04-12'): ")
    repo_articles = ArticlesRepository()
    repo_clean_articles = CleanArticlesRepository()
    repo_metadata = MetadataRepository()
    repo_summaries = SummariesRepository()
    service = ArticlesService(repo_summaries, repo_articles, repo_clean_articles, repo_metadata)
    print("Embedding model: sentence-transformers/all-MiniLM-L6-v2 (local cache)")
    processed_sample = service.clean_articles(sample_temp)
    print(f"Processing, embedding, and insertion of cleaned articles for batch {processed_sample} completed.")
    return processed_sample


if __name__ == "__main__":
    samples = ["1-2025-08-11", "1-2025-08-13", "1-2025-08-14", "1-2025-08-15", "1-2025-08-16"]
    for sample in samples:
        clean_articles(sample)
        print("All samples processed successfully.")
