"""Domain-level interfaces and services for working with articles."""
from urllib.parse import urlparse
from __future__ import annotations
from services.embeddings import embed_text
from pipeline_sample.summarizer import smart_summarize  # reuse your local summarizer
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

class SummariesRepositoryProtocol(Protocol):
    """Interface for storing and retrieving article summaries."""

    def create_articles(self, data: Dict[str, Any]) -> str: ...

    def get_articles(
            self,
            params: Dict[str, Any],
            projection: Optional[Dict[str, int]] = None,
    ) -> Iterable[Dict[str, Any]]: ...

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
            repo_summaries: SummariesRepositoryProtocol,
            repo_articles: ArticlesRepositoryProtocol,
            repo_clean_articles: CleanArticlesRepositoryProtocol,
            repo_metadata: MetadataRepositoryProtocol,
    ) -> None:
        self.repo_summaries = repo_summaries
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

    def _source_domain(self, url: str | None) -> str | None:
        if not url:
            return None
        try:
            host = urlparse(url).hostname or ""
            return host.lower()
        except Exception:
            return None

    def _choose_summary(self, article: Dict[str, Any]) -> str:
        # Prefer existing summary if your gather/classify wrote one.
        summary = (article.get("summary") or "").strip()
        if summary:
            return summary
        # Fallback: smart_summarize (already cached model)
        text = (article.get("text") or "").strip()
        if len(text) <= 200:
            return text
        return smart_summarize(text)

    def clean_articles(self, sample_id: str) -> str:
        """Clean raw articles for a given sample using the injected repositories."""
        count = 0
        self.repo_metadata.update_metadata(
            {"_id": sample_id},
            {"$set": {"cleaning_sample_startedAt": datetime.now(UTC)}},
        )

        for article in self.repo_articles.get_articles({"sample": sample_id}):
            text = (article.get("text") or "").strip()
            if not text:
                continue
            count += 1
            print(f"[{count}] Cleaning article: {article.get('title', 'No Title')}")

            # 1) linguistic features
            nouns = self.extract_nouns(text)

            # 2) summary for embedding
            summary = self._choose_summary(article)

            # 3) vector embedding on summary (normalize in service)
            vector = embed_text(summary)  # List[float32]

            # 4) handy domain
            domain = self._source_domain(article.get("url"))

            cleaned_doc: Dict[str, Any] = {
                "title": article.get("title"),
                "url": article.get("url"),
                "source": article.get("source"),
                "source_domain": domain,
                "scraped_at": article.get("scraped_at"),
                "published_at": article.get("published_at"),  # may be None
                "batch": article.get("batch"),
                "sample": sample_id,

                # analysis fields
                "topic": article.get("topic"),
                "sentiment": article.get("sentiment"),
                "nouns": nouns,
                "summary": summary,
                "embedding": vector,

                # processing flags
                "isProcessed": False,
                "isEmbedded": True,
                "isCleaned": True,
            }

            # mark raw article cleaned (keeps your current behavior)
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
