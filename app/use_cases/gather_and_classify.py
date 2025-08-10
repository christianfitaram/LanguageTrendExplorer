# app/use_cases/gather_and_classify.py
from __future__ import annotations
from collections import Counter
from datetime import datetime, UTC
from typing import Any, Dict, Iterable, Protocol

from services.classifier_service import ClassifierService, ArticleIn


# ---- Ports / Protocols ----
class ArticlesRepo(Protocol):
    def create_articles(self, data: Dict[str, Any]) -> str: ...


class LinkPoolGatePort(Protocol):
    """Small gate to centralize link_pool decisions."""
    def is_processed(self, url: str) -> bool: ...
    def ensure_tracked(self, url: str) -> None: ...
    def mark_processed(self, url: str, sample_id: str) -> None: ...


class MetadataRepo(Protocol):
    def insert_metadata(self, doc: Dict[str, Any]) -> str: ...
    def update_metadata(self, selector: Dict[str, Any], update: Dict[str, Any]) -> int: ...


class Batches(Protocol):
    def next_batch_number(self) -> int: ...


class Samples(Protocol):
    def new_sample_id(self) -> str: ...
    def find_last_sample(self) -> str | None: ...
    def link_previous(self, prev: str | None, current: str) -> None: ...


class Scraper(Protocol):
    """Yields dicts with keys: title, url, text, source, scraped_at."""
    def stream(self) -> Iterable[Dict[str, Any]]: ...


# ---- Use Case ----
class GatherAndClassifyUseCase:
    def __init__(
        self,
        articles_repo: ArticlesRepo,
        metadata_repo: MetadataRepo,
        batches: Batches,
        samples: Samples,
        classifier: ClassifierService,
        scrapers: list[Scraper],
        link_pool_gate: LinkPoolGatePort,   # <-- inject the gate instead of touching repo directly
    ) -> None:
        self.articles_repo = articles_repo
        self.metadata_repo = metadata_repo
        self.batches = batches
        self.samples = samples
        self.classifier = classifier
        self.scrapers = scrapers
        self.link_pool_gate = link_pool_gate

    def run(self) -> str:
        batch = self.batches.next_batch_number()
        sample = self.samples.new_sample_id()
        prev = self.samples.find_last_sample()

        # Create/initialize metadata for this sample
        self.metadata_repo.insert_metadata({
            "_id": sample,
            "gathering_sample_startedAt": datetime.now(UTC),
            "batch": batch,
            "prev": prev,
            "next": None,
        })
        self.samples.link_previous(prev, sample)

        # Counters
        seen: set[str] = set()
        topic_counter: Counter[str] = Counter()
        sentiment_counter: Counter[str] = Counter()
        ok, fail = 0, 0

        for scraper in self.scrapers:
            for raw in scraper.stream():
                url = raw.get("url")
                text = (raw.get("text") or "").strip()
                if not url or not text:
                    continue
                if url in seen:
                    continue
                seen.add(url)

                # Centralized link-pool logic
                if self.link_pool_gate.is_processed(url):
                    continue
                self.link_pool_gate.ensure_tracked(url)

                try:
                    art_in = ArticleIn(
                        title=raw.get("title"),
                        url=url,
                        text=text,
                        source=raw.get("source"),
                        scraped_at=raw.get("scraped_at"),
                    )
                    classified = self.classifier.classify(art_in, batch=batch, sample=sample)

                    # persist the article
                    self.articles_repo.create_articles(classified.__dict__)

                    # mark processed for this sample
                    self.link_pool_gate.mark_processed(url, sample)

                    ok += 1
                    topic_counter[classified.topic] += 1
                    sentiment_counter[classified.sentiment.get("label", "unknown")] += 1

                except Exception:
                    fail += 1
                    # Avoid reprocessing loops on failures, still mark as processed in this sample
                    self.link_pool_gate.mark_processed(url, sample)

        # Distributions
        total = sum(topic_counter.values()) or 1
        topic_pct = [{"label": t, "percentage": round((c / total) * 100, 2)} for t, c in topic_counter.most_common()]
        sentiment_pct = [{"label": s, "percentage": round((c / total) * 100, 2)} for s, c in sentiment_counter.most_common()]

        # Finalize metadata
        self.metadata_repo.update_metadata(
            {"_id": sample},
            {
                "$set": {
                    "articles_processed": {"successfully": ok, "unsuccessfully": fail},
                    "topic_distribution": topic_pct,
                    "sentiment_distribution": sentiment_pct,
                    "gathering_sample_finishedAt": datetime.now(UTC),
                }
            },
        )
        return sample
