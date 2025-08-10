"""Domain-level interfaces and services for working with articles."""

from __future__ import annotations
from datetime import datetime, UTC
from typing import Protocol, Dict, Any, Iterable, Optional, List
import spacy

# Exposed names
__all__ = [
    "ArticlesRepositoryProtocol",
    "CleanArticlesRepositoryProtocol",
    "MetadataRepositoryProtocol",
    "ArticlesService",
]


class ArticlesRepositoryProtocol(Protocol):
    """Interface for storing and retrieving full articles."""

    def create_articles(self, data: Dict[str, Any]) -> str: ...

    def get_articles(
            self,
            params: Dict[str, Any],
            projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[Dict[str, Any]]: ...

    def update_articles(self, selector: Dict[str, Any], update_data: Dict[str, Any]) -> int: ...


class CleanArticlesRepositoryProtocol(Protocol):
    """Interface for storing cleaned article documents."""

    def create_articles(self, data: Dict[str, Any]) -> str: ...


class MetadataRepositoryProtocol(Protocol):
    """Interface for reading and updating metadata documents."""

    def update_metadata(self, selector: Dict[str, Any], update_data: Dict[str, Any]) -> int: ...


class ArticlesService:
    """High‑level operations on articles."""

    def __init__(
            self,
            repo_articles: ArticlesRepositoryProtocol,
            repo_clean_articles: CleanArticlesRepositoryProtocol,
            repo_metadata: MetadataRepositoryProtocol,
    ) -> None:
        self.repo_articles = repo_articles
        self.repo_clean_articles = repo_clean_articles
        self.repo_metadata = repo_metadata
        self.nlp = spacy.load("en_core_web_sm")

    def extract_nouns(self, text: str) -> List[str]:
        """Return a list of lemmatised, lowercase nouns from the given text."""
        doc = self.nlp(text)
        return [
            token.lemma_.lower()
            for token in doc
            if token.pos_ == "NOUN" and not token.is_stop and token.is_alpha
        ]

    def clean_articles(self, sample_id: str) -> str:
        """Clean raw articles for a given sample using the injected repositories."""
        self.repo_metadata.update_metadata(
            {"_id": sample_id},
            {"$set": {"cleaning_sample_startedAt": datetime.now(UTC)}},
        )
        for article in self.repo_articles.get_articles({"sample": sample_id}):
            if not article.get("text"):
                continue
            nouns = self.extract_nouns(article["text"])
            cleaned_doc: Dict[str, Any] = {
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source"),
                "scraped_at": article.get("scraped_at"),
                "batch": article.get("batch"),
                "isProcessed": False,
                "topic": article.get("topic"),
                "sentiment": article.get("sentiment"),
                "sample": sample_id,
                "nouns": nouns,
            }
            self.repo_articles.update_articles(
                {"_id": article.get("_id")},
                {"$set": {"isCleaned": True}},
            )
            self.repo_clean_articles.create_articles(cleaned_doc)
        self.repo_metadata.update_metadata(
            {"_id": sample_id},
            {"$set": {"cleaning_sample_finishedAt": datetime.now(UTC)}},
        )
        return sample_id
