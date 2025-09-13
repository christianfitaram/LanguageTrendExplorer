# pipeline_sample/exec_trends.py
from __future__ import annotations
from typing import Optional
from datetime import datetime, UTC

# Repos (clean + trends)
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.trend_threads_repository import TrendThreadsRepository
from lib.repositories.daily_trends_repository import DailyTrendsRepository

# Use cases (built in earlier phases)
from app.use_cases.build_daily_clusters import BuildDailyClustersUseCase
from app.use_cases.rank_clusters import RankClustersUseCase
from app.use_cases.link_threads import LinkThreadsUseCase

# Helper to default to last sample if not provided
from services.metadata import find_last_sample


def main(
        sample_id: Optional[str] = None,
        limit: int = 15,
        persist: bool = True,  # --persist / --dry-run
        date: Optional[str] = None,  # YYYY-MM-DD (defaults to today UTC)
        print_top: int = 5
) -> int:
    # Resolve sample + date
    sample = sample_id or find_last_sample()
    if not sample:
        print("No sample provided and none found in metadata. Aborting.")
        return 1
    date_iso = date or datetime.now(UTC).date().isoformat()

    # Repos
    clean_repo = CleanArticlesRepository()
    threads_repo = TrendThreadsRepository()
    daily_repo = DailyTrendsRepository()

    # Phase 2: build clusters
    builder = BuildDailyClustersUseCase(clean_repo)
    built = builder.run(sample)
    clusters = built.get("clusters", [])
    if not clusters:
        print(f"No clusters for sample {sample}.")
        return 0

    # Phase 3: rank clusters (importance)
    ranker = RankClustersUseCase(clean_repo)
    ranked = ranker.run(sample, clusters)

    # Phase 4: link threads (EMA + novelty)
    linker = LinkThreadsUseCase(
        clean_repo=clean_repo,
        threads_repo=threads_repo if persist else _NoopThreadsRepo(),
        daily_repo=daily_repo if persist else _NoopDailyRepo(),
    )
    linked = linker.run(sample_id=sample, date_iso=date_iso, ranked_clusters=ranked.clusters)

    # Console output
    print(f"\nTop threads for {date_iso} (sample {sample})")
    print("==========================================")
    for t in linked.threads[:max(0, print_top)]:
        score = round(t["trend_score"], 2)
        size = t["size"]
        label = t.get("topic_label") or "—"
        print(f"{score:>6} | size {size:<3} | {label}")

    if not persist:
        print("\n(dry-run) Nothing persisted.")
    else:
        print("\nPersisted to: trend_threads + daily_trends")
    return 0


# --- No-op adapters for --dry-run mode ---
class _NoopThreadsRepo:
    def get_threads_on(self, date_iso: str):
        return []

    def get_recent_for_thread(self, thread_id: str, since_iso: str):
        return []

    def upsert_today(self, selector, doc):
        pass


class _NoopDailyRepo:
    def upsert_daily(self, selector, doc):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
