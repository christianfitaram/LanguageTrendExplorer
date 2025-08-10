from datetime import datetime, UTC, time, timedelta
import spacy
from collections import Counter, defaultdict
import pandas as pd
from lib.repositories.clean_articles_repository import CleanArticlesRepository
from lib.repositories.metadata_repository import MetadataRepository
from lib.repositories.daily_trends_repository import DailyTrendsRepository
from utils.validation import is_valid_sample

nlp = spacy.load("en_core_web_sm")

repo_clean_art = CleanArticlesRepository()
repo_metadata = MetadataRepository()
repo_daily_trends = DailyTrendsRepository()


def calculate_distribution(values):
    counter = Counter(values)
    total = sum(counter.values())
    return [
        {"label": label, "percentage": round((count / total) * 100)}
        for label, count in counter.most_common()
    ]


def analyze_sample_trends(sample_id=None):
    if sample_id is None:
        sample_id = input("Enter the sample string (e.g. '1-2025-04-12'): ")
        while is_valid_sample(sample_id) is False:
            sample_id = input("Incorrect format (e.g. '1-2025-04-12'): ")

    today = datetime.now(UTC).date()
    articles = list(repo_clean_art.get_articles({
        "sample": sample_id
    }))

    if not articles:
        print("No articles found for today.")
        return
    print(f"✅ Found {len(articles)} articles to process ")
    word_occurrences = []
    repo_metadata.update_metadata({"_id": sample_id}, {"$set": {"analyze_sample_startedAt": datetime.now(UTC)}})
    for article in articles:
        topic = article.get("topic", "").strip().lower()
        sentiment_label = article.get("sentiment", {}).get("label", "").strip().lower()
        nouns = article.get("nouns", [])

        # Filter invalid topic/sentiment values
        is_valid_topic = topic not in {"", "topic", "unknown", "none"}
        is_valid_sentiment = sentiment_label not in {"", "n/a", "label", "unknown", "none"}

        for noun in nouns:
            word_occurrences.append({
                "word": noun,
                "topic": topic if is_valid_topic else None,
                "sentiment": sentiment_label if is_valid_sentiment else None
            })

        is_updated = repo_clean_art.update_articles({"_id": article["_id"]}, {"$set": {"isProcessed": True}})

        if is_updated > 0:
            print(f"ARTICLE: {article["title"]} has been processed successfully")
        else:
            print(f"ARTICLE: {article["title"]} has not been labeled as processed")

    # Step 1: Count frequencies and set metadata
    word_counter = Counter([entry["word"] for entry in word_occurrences])

    # Total number of words (including duplicates)
    total_words = sum(word_counter.values())

    # Number of distinct words
    distinct_words = len(word_counter)
    repo_metadata.update_metadata({"_id": sample_id}, {
        "$set": {"raw_total_words": total_words, "distinct_words": distinct_words}})
    top_words = word_counter.most_common(15)

    # Step 2: Group context by word
    topic_by_word = defaultdict(list)
    sentiment_by_word = defaultdict(list)

    for entry in word_occurrences:
        if entry["topic"]:
            topic_by_word[entry["word"]].append(entry["topic"])
        if entry["sentiment"]:
            sentiment_by_word[entry["word"]].append(entry["sentiment"])

    # Step 3: Create structured output
    ranked_words = []
    for idx, (word, count) in enumerate(top_words):
        ranked_words.append({
            "word": word,
            "count": count,
            "rank": idx + 1,
            "context": {
                "topics": calculate_distribution(topic_by_word[word]),
                "sentiments": calculate_distribution(sentiment_by_word[word])
            }
        })

    repo_daily_trends.insert_daily_trends({
        "date": today.isoformat(),
        "top_words": ranked_words,
        "created_at": datetime.now(UTC),
        "sample": sample_id
    })
    repo_metadata.update_metadata({"_id": sample_id}, {"$set": {"analyze_sample_finishedAt": datetime.now(UTC)}})

    print(pd.DataFrame(ranked_words))


if __name__ == "__main__":
    analyze_sample_trends()
