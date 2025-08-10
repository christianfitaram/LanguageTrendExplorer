# pipeline_sample/exec_gather.py
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()
import argparse
import os
from pathlib import Path

# scrapers (pure)
from custom_scrapers import scrape_bbc_stream, scrape_cnn_stream, scrape_wsj_stream, scrape_aljazeera
from news_api_scraper import scrape_newsapi_stream, scrape_all_categories

# domain/app
from services.classifier_service import ClassifierService
from app.use_cases.gather_and_classify import GatherAndClassifyUseCase

# repos
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.link_pool_repository import LinkPoolRepository
from lib.repositories.metadata_repository import MetadataRepository

# helpers
from services.batches import get_next_batch_number
from services.ids import generate_id
from services.metadata import find_last_sample, update_next_in_previous_doc

# adapters
from adapters.scrapers import FunctionScraper
from adapters.pipelines import HFPipelines
from adapters.link_pool_gate import LinkPoolGate  # <-- NEW

# HF setup (local cache)
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline as hf_pipeline

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
MODEL_NAME_TOPIC = "facebook/bart-large-mnli"
_CACHE_DIR = Path(os.getenv("HF_HOME", os.getenv("TRANSFORMERS_CACHE", "models/transformers"))).resolve()

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=str(_CACHE_DIR), local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, cache_dir=str(_CACHE_DIR), local_files_only=True)
sentiment_pipeline = hf_pipeline(task="sentiment-analysis", model=model, tokenizer=tokenizer)

tokenizer_topic = AutoTokenizer.from_pretrained(MODEL_NAME_TOPIC, cache_dir=str(_CACHE_DIR), local_files_only=True)
model_topic = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME_TOPIC, cache_dir=str(_CACHE_DIR), local_files_only=True)
topic_pipeline = hf_pipeline(task="zero-shot-classification", model=model_topic, tokenizer=tokenizer_topic)

CANDIDATE_TOPICS = [
    "politics and government", "sports and athletics", "science and research", "technology and innovation",
    "health and medicine", "business and finance", "entertainment and celebrity", "crime and justice",
    "climate and environment", "education and schools", "war and conflict", "travel and tourism",
]


def _build_scrapers(newsapi_only: bool) -> list[FunctionScraper]:
    if newsapi_only:
        return [
            FunctionScraper(lambda: scrape_newsapi_stream()),
            FunctionScraper(lambda: scrape_all_categories()),
        ]
    return [
        FunctionScraper(lambda: scrape_cnn_stream()),
        FunctionScraper(lambda: scrape_bbc_stream()),
        FunctionScraper(lambda: scrape_wsj_stream()),
        FunctionScraper(lambda: scrape_aljazeera()),
        FunctionScraper(lambda: scrape_newsapi_stream()),
        FunctionScraper(lambda: scrape_all_categories()),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape + classify + persist")
    parser.add_argument("--newsapi-only", dest="newsapi_only", action="store_true",
                        help="Use only NewsAPI-based scrapers")
    args = parser.parse_args()

    scrapers = _build_scrapers(args.newsapi_only)

    # Build pipelines + classifier
    pipes = HFPipelines(sentiment_pipeline, topic_pipeline, CANDIDATE_TOPICS)
    classifier = ClassifierService(pipes, candidate_topics=CANDIDATE_TOPICS)

    # Repos
    repo_articles = ArticlesRepository()
    repo_link_pool = LinkPoolRepository()
    repo_metadata = MetadataRepository()

    # Link-pool gate (centralizes dedup/processed flags)
    gate = LinkPoolGate(repo_link_pool)

    # Small adapters for your batch/sample helpers
    class _Batches:
        def next_batch_number(self) -> int:
            return get_next_batch_number(repo=repo_articles)

    class _Samples:
        def new_sample_id(self) -> str:
            return generate_id(repo=repo_articles)
        def find_last_sample(self):
            return find_last_sample()
        def link_previous(self, prev, current):
            update_next_in_previous_doc(prev, current)

    # Use-case orchestrates everything (CLI doesn’t touch repos directly)
    usecase = GatherAndClassifyUseCase(
        articles_repo=repo_articles,
        metadata_repo=repo_metadata,
        batches=_Batches(),
        samples=_Samples(),
        classifier=classifier,
        scrapers=scrapers,
        link_pool_gate=gate,   # <-- NEW
    )

    sample_id = usecase.run()
    print(f"✅ Gather+Classify completed. Sample: {sample_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
