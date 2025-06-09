# classifier.py
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from exec_scraper import get_all_articles
from summarizer import smart_summarize
from datetime import datetime, UTC
from collections import Counter
from mongo.mongodb_client import db
from mongo.repositories.repository_articles import RepositoryArticles
from mongo.repositories.repository_link_pool import RepositoryLinkPool
from mongo.repositories.repository_metadata import RepositoryMetadata

# Injecting repositories
repo_articles = RepositoryArticles(db)
repo_link_pool = RepositoryLinkPool(db)
repo_metadata = RepositoryMetadata(db)

# Define your candidate labels (topics)
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
    "travel and tourism"
]

# Load HuggingFace sentiment_pipeline
MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
CACHE_DIR = "../models/transformers"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)

sentiment_pipeline = pipeline(
    "sentiment-analysis",
    model=model,
    tokenizer=tokenizer
)

# Load HuggingFace topic_pipeline
MODEL_NAME_TOPIC = "facebook/bart-large-mnli"
CACHE_DIR_TOPIC = "../models/transformers"

tokenizer_topic = AutoTokenizer.from_pretrained(MODEL_NAME_TOPIC, cache_dir=CACHE_DIR_TOPIC)
model_topic = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME_TOPIC, cache_dir=CACHE_DIR_TOPIC)

topic_pipeline = pipeline(
    "zero-shot-classification",
    model=model_topic,
    tokenizer=tokenizer_topic
)


def get_next_batch_number():
    # Get the current date in UTC
    today = datetime.now(UTC).date()

    # Attempt to find the latest document for today, sorted by batch number in descending order
    latest_doc = repo_articles.get_one_article(
        {"scraped_at": {"$gte": datetime.combine(today, datetime.min.time(), UTC)}},
        [("batch", -1)])

    # If a document is found and, it has a 'batch' field, increment its batch number
    if latest_doc and "batch" in latest_doc:
        return latest_doc["batch"] + 1
    # If no document is found for today, start with batch number 1
    return 1


def testing_id_generator():
    today = datetime.now(UTC).date()
    batch = get_next_batch_number()

    id_new = f"{batch}-{today}"

    return id_new


def classify_articles():
    sentiment_counter = Counter()
    topic_counter = Counter()
    num_well_classified = 0
    num_failed_classified = 0
    batch_number = get_next_batch_number()
    id_for_metadata = testing_id_generator()

    print(f"🗂️Starting batch ID: {id_for_metadata}")
    repo_metadata.insert_metadata(
        {"_id": id_for_metadata, "gathering_sample_startedAt": datetime.now(UTC), "batch": batch_number})

    for i, article in enumerate(get_all_articles(), start=1):
        text = article.get("text", "")
        text_len = len(text)
        if not text:
            continue

        try:
            if text_len > 200:
                summary = smart_summarize(text)
            else:
                summary = text

            topic = topic_pipeline(summary, candidate_labels=CANDIDATE_TOPICS)
            sentiment = sentiment_pipeline(summary)[0]

            classified_article = {
                "title": article.get("title"),
                "url": article.get("url"),
                "text": article.get("text"),
                "source": article.get("source"),
                "scraped_at": article.get("scraped_at"),
                "batch": batch_number,
                "topic": topic["labels"][0],
                "isCleaned": False,
                "sentiment": {
                    "label": sentiment["label"],
                    "score": sentiment["score"]
                },
                "sample": id_for_metadata
            }

            # set data for metadata
            num_well_classified += 1
            topic_label = topic["labels"][0]
            sentiment_label = sentiment["label"]
            topic_counter[topic_label] += 1
            sentiment_counter[sentiment_label] += 1

            # inserting data into mongoDB
            repo_articles.create_articles(classified_article)

            repo_link_pool.update_link_in_pool({"url": article.get("url")},
                                               {"$set": {"is_articles_processed": True, "in_sample": id_for_metadata}})

            print(f"[{i}] ✅ Inserted (In sample {id_for_metadata}): {classified_article['title']}")

        except Exception as e:
            num_failed_classified += 1
            repo_link_pool.update_link_in_pool({"url": article.get("url")},
                                               {"$set": {"is_articles_processed": True, "in_sample": id_for_metadata}})
            print(f"[{i}] ❌ Error classifying article: {e}")

    # Total number of successfully classified articles
    total_classified = sum(topic_counter.values())

    # Compute sorted percentages
    topic_percentages = [
        {"label": label, "percentage": round((count / total_classified) * 100, 2)}
        for label, count in topic_counter.most_common()
    ]

    sentiment_percentages = [
        {"label": label, "percentage": round((count / total_classified) * 100, 2)}
        for label, count in sentiment_counter.most_common()
    ]
    repo_metadata.update_metadata({"_id": id_for_metadata}, {
        "$set": {
            "articles_processed": {
                "successfully": num_well_classified,
                "unsuccessfully": num_failed_classified
            },
            "topic_distribution": topic_percentages,
            "sentiment_distribution": sentiment_percentages,
            "gathering_sample_finishedAt": datetime.now(UTC)
        }
    })

    return id_for_metadata


if __name__ == "__main__":
    classify_articles()
