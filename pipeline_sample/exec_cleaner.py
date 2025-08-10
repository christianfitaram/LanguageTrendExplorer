"""CLI entry point for cleaning articles."""
from __future__ import annotations
from typing import Optional
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from utils.validation import is_valid_sample
from services.articles import ArticlesService


def clean_articles(sample_temp: Optional[str] = None) -> str:
    if sample_temp is None:
        sample_temp = input("Enter the sample string (e.g. '1-2025-04-12'): ")
        while not is_valid_sample(sample_temp):
            sample_temp = input("Incorrect format (e.g. '1-2025-04-12'): ")
    repo_articles = ArticlesRepository()
    repo_clean_articles = CleanArticlesRepository()
    repo_metadata = MetadataRepository()
    service = ArticlesService(repo_articles, repo_clean_articles, repo_metadata)
    processed_sample = service.clean_articles(sample_temp)
    print(f"Processing and insertion of cleaned articles for batch {processed_sample} completed.")
    return processed_sample


if __name__ == "__main__":
    clean_articles()
