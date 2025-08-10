# services/classifier_service.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, Protocol

from pipeline_sample.summarizer import smart_summarize


@dataclass(frozen=True)
class Pipelines(Protocol):
    def sentiment(self, text: str) -> Dict[str, Any]: ...
    def topic(self, text: str) -> Dict[str, Any]: ...


@dataclass(frozen=True)
class ArticleIn:
    title: Optional[str]
    url: str
    text: str
    source: Optional[str]
    scraped_at: Any  # datetime


@dataclass(frozen=True)
class ArticleOut:
    title: Optional[str]
    url: str
    text: str
    source: Optional[str]
    scraped_at: Any
    batch: int
    topic: str
    isCleaned: bool
    sentiment: Dict[str, Any]
    sample: str


class ClassifierService:
    """Pure(ish) classify: doesn’t touch DB. Pipelines are injected."""

    def __init__(self, pipelines: Pipelines, candidate_topics: list[str]) -> None:
        self.pipes = pipelines
        self.candidate_topics = candidate_topics

    def classify(self, art: ArticleIn, batch: int, sample: str) -> ArticleOut:
        text_for_cls = art.text if len(art.text) <= 200 else self._summarize_cheap(art.text)
        topic = self.pipes.topic(text_for_cls)           # expects {"labels":[...], ...}
        sentiment = self.pipes.sentiment(text_for_cls)   # expects {"label": "...", "score": ...}

        topic_label = topic["labels"][0] if topic.get("labels") else "unknown"

        return ArticleOut(
            title=art.title,
            url=art.url,
            text=art.text,
            source=art.source,
            scraped_at=art.scraped_at,
            batch=batch,
            topic=topic_label,
            isCleaned=False,
            sentiment=sentiment,
            sample=sample,
        )

    def _summarize_cheap(self, text: str) -> str:
        smart_summarize(text)
