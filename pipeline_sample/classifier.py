# pipeline_sample/classifier.py
from collections import Counter
from datetime import datetime, timezone
import os
from pathlib import Path

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

from custom_pipeline.get_all_articles import get_all_articles
from custom_pipeline.summarizer import smart_summarize

# New repositories (centralized client under the hood)
from lib.repositories.articles_repository import ArticlesRepository
from lib.repositories.link_pool_repository import LinkPoolRepository
from lib.repositories.metadata_repository import MetadataRepository

# Services (DI-ready)
from services.batches import get_next_batch_number
from services.ids import generate_id
from services.metadata import find_last_sample, update_next_in_previous_doc

# -----------------------------------------------------------------------------
# Config for Hugging Face cache
# -----------------------------------------------------------------------------
_CACHE_DIR = Path(
    os.getenv("HF_HOME", os.getenv("TRANSFORMERS_CACHE", "models/transformers"))
).resolve()

# -----------------------------------------------------------------------------
# Candidate topics
# -----------------------------------------------------------------------------
CANDIDATE_TOPICS = [
    "politics and government",
    "sports and athletics",
    "science and research",
    "technology and innovation",
    "health and medicine",
    "business and finance",
    "entertainment and celebrity",
    "crime and justice",
    "climate and environment",
    "education and schools",
    "war and conflict",
    "travel and tourism",
]

# -----------------------------------------------------------------------------
# HuggingFace models & pipelines (offline-first)
# -----------------------------------------------------------------------------
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME, cache_dir=str(_CACHE_DIR), local_files_only=True
)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, cache_dir=str(_CACHE_DIR), local_files_only=True
)
sentiment_pipeline = pipeline(
    task="sentiment-analysis",
    model=model,
    tokenizer=tokenizer,
)

MODEL_NAME_TOPIC = "facebook/bart-large-mnli"
tokenizer_topic = AutoTokenizer.from_pretrained(
    MODEL_NAME_TOPIC, cache_dir=str(_CACHE_DIR), local_files_only=True
)
model_topic = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME_TOPIC, cache_dir=str(_CACHE_DIR), local_files_only=True
)
topic_pipeline = pipeline(
    task="zero-shot-classification",
    model=model_topic,
    tokenizer=tokenizer_topic,
)


# -----------------------------------------------------------------------------
# Main classification function
# -----------------------------------------------------------------------------
def classify_articles():
    # Repos (could be injected if you prefer)
    repo_articles = ArticlesRepository()
    repo_link_pool = LinkPoolRepository()
    repo_metadata = MetadataRepository()

    sentiment_counter = Counter()
    topic_counter = Counter()
    num_well_classified = 0
    num_failed_classified = 0

    # Use services (DI: pass repos if you want deterministic tests)
    batch_number = get_next_batch_number(repo=repo_articles)
    id_for_metadata = generate_id(repo=repo_articles)
    prev_sample = find_last_sample()  # adapter wraps MetadataRepository by default

    print(f"🗂️ Starting batch ID: {id_for_metadata}")

    repo_metadata.insert_metadata({
        "_id": id_for_metadata,
        "gathering_sample_startedAt": datetime.now(timezone.utc),
        "batch": batch_number,
        "prev": prev_sample,
        "next": None,
    })

    # Link this sample to the previous
    update_next_in_previous_doc(prev_sample,id_for_metadata )

    for i, article in enumerate(get_all_articles(), start=1):
        text = article.get("text", "") or ""
        if not text:
            continue

        try:
            summary = smart_summarize(text) if len(text) > 200 else text

            topic = topic_pipeline(summary, candidate_labels=CANDIDATE_TOPICS)
            sentiment = sentiment_pipeline(summary)[0]

            topic_label = topic["labels"][0]
            sentiment_label = sentiment["label"]

            classified_article = {
                "title": article.get("title"),
                "url": article.get("url"),
                "text": text,
                "source": article.get("source"),
                "scraped_at": article.get("scraped_at"),
                "batch": batch_number,
                "topic": topic_label,
                "isCleaned": False,
                "sentiment": {
                    "label": sentiment_label,
                    "score": sentiment["score"],
                },
                "sample": id_for_metadata,
            }

            # Update counters
            num_well_classified += 1
            topic_counter[topic_label] += 1
            sentiment_counter[sentiment_label] += 1

            # Persist
            repo_articles.create_articles(classified_article)
            repo_link_pool.update_link_in_pool(
                {"url": article.get("url")},
                {"$set": {"is_articles_processed": True, "in_sample": id_for_metadata}},
            )

            print(f"[{i}] ✅ Inserted (sample {id_for_metadata}): {classified_article['title']}")

        except Exception as e:
            num_failed_classified += 1
            # Still mark the link as processed/in-sample to avoid reprocessing loops
            repo_link_pool.update_link_in_pool(
                {"url": article.get("url")},
                {"$set": {"is_articles_processed": True, "in_sample": id_for_metadata}},
            )
            print(f"[{i}] ❌ Error classifying article: {e}")

    total_classified = sum(topic_counter.values()) or 1  # avoid zero-division

    topic_percentages = [
        {"label": label, "percentage": round((count / total_classified) * 100, 2)}
        for label, count in topic_counter.most_common()
    ]

    sentiment_percentages = [
        {"label": label, "percentage": round((count / total_classified) * 100, 2)}
        for label, count in sentiment_counter.most_common()
    ]

    repo_metadata.update_metadata(
        {"_id": id_for_metadata},
        {
            "$set": {
                "articles_processed": {
                    "successfully": num_well_classified,
                    "unsuccessfully": num_failed_classified,
                },
                "topic_distribution": topic_percentages,
                "sentiment_distribution": sentiment_percentages,
                "gathering_sample_finishedAt": datetime.now(timezone.utc),
            }
        },
    )

    return id_for_metadata


if __name__ == "__main__":
    classify_articles()
