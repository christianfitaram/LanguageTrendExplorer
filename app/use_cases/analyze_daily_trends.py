# app/use_cases/analyze_daily_trends.py
from __future__ import annotations
from datetime import datetime, UTC
from typing import Dict, Any, Optional, Iterable, Protocol, List

from services.daily_trends import DailyTrendsService


class CleanArticlesRepo(Protocol):
    def get_articles(self, params: Dict[str, Any]) -> Iterable[Dict[str, Any]]: ...

    def update_articles(self, selector: Dict[str, Any], update: Dict[str, Any]) -> int: ...


class MetadataRepo(Protocol):
    def update_metadata(self, selector: Dict[str, Any], update: Dict[str, Any]) -> int: ...


class DailyTrendsRepo(Protocol):
    def insert_daily_trends(self, doc: Dict[str, Any]) -> str: ...


class AnalyzeDailyTrendsUseCase:
    """
    Application layer (imperative orchestration, I/O):
    - Reads from repos, writes metrics & results, updates processed flags.
    - Delegates pure computation to DailyTrendsService.
    """

    def __init__(
            self,
            clean_repo: CleanArticlesRepo,
            meta_repo: MetadataRepo,
            trends_repo: DailyTrendsRepo,
            service: Optional[DailyTrendsService] = None,
    ) -> None:
        self.clean_repo = clean_repo
        self.meta_repo = meta_repo
        self.trends_repo = trends_repo
        self.service = service or DailyTrendsService()

    def run(
            self,
            sample_id: str,
            limit: int = 15,
            persist: bool = False,
            mark_processed: bool = False,
    ) -> Dict[str, Any]:
        self.meta_repo.update_metadata(
            {"_id": sample_id}, {"$set": {"analyze_sample_startedAt": datetime.now(UTC)}}
        )

        articles = list(self.clean_repo.get_articles({"sample": sample_id}))
        if not articles:
            # still mark finished to avoid dangling "startedAt"
            self.meta_repo.update_metadata(
                {"_id": sample_id}, {"$set": {"analyze_sample_finishedAt": datetime.now(UTC)}}
            )
            return {"sample": sample_id, "ranked_words": [], "metrics": {"total_words": 0, "distinct_words": 0}}

        result = self.service.compute(articles, limit=limit)
        metrics = result["metrics"]
        ranked = result["ranked_words"]

        # write metrics
        self.meta_repo.update_metadata(
            {"_id": sample_id},
            {"$set": {"raw_total_words": metrics["total_words"], "distinct_words": metrics["distinct_words"]}},
        )

        # mark processed if asked
        if mark_processed:
            for a in articles:
                self.clean_repo.update_articles({"_id": a["_id"]}, {"$set": {"isProcessed": True}})

        # persist trends if asked
        if persist:
            self.trends_repo.insert_daily_trends({
                "date": datetime.now(UTC).date().isoformat(),
                "top_words": ranked,
                "created_at": datetime.now(UTC),
                "sample": sample_id,
            })

        self.meta_repo.update_metadata(
            {"_id": sample_id}, {"$set": {"analyze_sample_finishedAt": datetime.now(UTC)}}
        )

        return {"sample": sample_id, **result}
