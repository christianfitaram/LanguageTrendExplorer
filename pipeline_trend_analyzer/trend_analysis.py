# pipeline_sample/exec_trends.py
from __future__ import annotations
import argparse
import pandas as pd

from utils.validation import is_valid_sample
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from lib.repositories.daily_trends_repository import DailyTrendsRepository
from app.use_cases.analyze_daily_trends import AnalyzeDailyTrendsUseCase


def _resolve_sample(sample: str | None) -> str:
    if sample and is_valid_sample(sample):
        return sample
    s = input("Enter the sample string (e.g. '1-2025-04-12'): ")
    while not is_valid_sample(s):
        s = input("Incorrect format (e.g. '1-2025-04-12'): ")
    return s


def main() -> int:
    p = argparse.ArgumentParser(description="Analyze daily trends for a sample.")
    p.add_argument("-s", "--sample")
    p.add_argument("-n", "--limit", type=int, default=15)
    p.add_argument("--persist", action="store_true", help="Persist the daily trends document")
    p.add_argument("--mark-processed", action="store_true", help="Mark articles as processed")
    p.add_argument("--no-print", action="store_true", help="Do not print the ranked words preview")
    args = p.parse_args()

    sample_id = _resolve_sample(args.sample)

    usecase = AnalyzeDailyTrendsUseCase(
        clean_repo=CleanArticlesRepository(),
        meta_repo=MetadataRepository(),
        trends_repo=DailyTrendsRepository(),
    )

    result = usecase.run(
        sample_id=sample_id,
        limit=args.limit,
        persist=args.persist,
        mark_processed=args.mark_processed,
    )

    if not args.no_print:
        print(pd.DataFrame(result["ranked_words"]))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
