from datetime import datetime, UTC, time, timedelta

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import spacy
from collections import Counter, defaultdict
import pandas as pd
from mongo.insert import insert_daily_trends
from mongo.find import find_clean_articles, find_daily_trends
from mongo.update import update_clean_articles, update_metadata

nlp = spacy.load("en_core_web_sm")


def calculate_distribution(values):
    counter = Counter(values)
    total = sum(counter.values())
    return [
        {"label": label, "percentage": round((count / total) * 100)}
        for label, count in counter.most_common()
    ]


def analyze_sample_trends(sample_id):
    today = datetime.now(UTC).date()
    articles = list(find_clean_articles({
        "sample": sample_id,
        "isProcessed": False,
    }))

    if not articles:
        print("No articles found for today.")
        return

    word_occurrences = []
    update_metadata({"_id":sample_id},{"$set":{"analyze_sample_startedAt":datetime.now(UTC)}})
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

        is_updated = update_clean_articles({"_id": article["_id"]}, {"$set": {"isProcessed": True}})

        if is_updated:
            print(f"ARTICLE: {article["title"]} has been processed successfully")
        else:
            print(f"ARTICLE: {article["title"]} has not been labeled as processed")

    # Step 1: Count frequencies and set metadata
    word_counter = Counter([entry["word"] for entry in word_occurrences])

    # Total number of words (including duplicates)
    total_words = sum(word_counter.values())

    # Number of distinct words
    distinct_words = len(word_counter)
    update_metadata({"_id": sample_id}, {
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
            "contexto": {
                "topics": calculate_distribution(topic_by_word[word]),
                "sentiments": calculate_distribution(sentiment_by_word[word])
            },
            "sample":sample_id
        })

    insert_daily_trends({
        "date": today.isoformat(),
        "top_words": ranked_words,
        "created_at": datetime.now(UTC)
    })
    update_metadata({"_id":sample_id},{"$set":{"analyze_sample_finishedAt":datetime.now(UTC)}})

    print(pd.DataFrame(ranked_words))


def get_today_trends():
    today = datetime.now(UTC).date()
    trend_doc = find_daily_trends("one", {"date": today.isoformat()})
    if not trend_doc:
        return None  # or return [] if you prefer empty list fallback
    return {
        "date": trend_doc["date"],
        "top_words": trend_doc["top_words"]
    }


def get_trends_by_date(date_str):
    """Fetch daily_trends document by ISO date string: YYYY-MM-DD"""
    trend_doc = find_daily_trends("one", {"date": date_str})

    if not trend_doc:
        return None

    return {
        "date": trend_doc["date"],
        "top_words": trend_doc["top_words"]
    }


def compare_trends_extended():
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)

    today_doc = find_daily_trends("one", {"date": today.isoformat()})
    yest_doc = find_daily_trends("one", {"date": yesterday.isoformat()})

    if not today_doc or not yest_doc:
        print("Missing trend data for today or yesterday.")
        return {}

    today_map = {entry["word"]: entry for entry in today_doc["top_words"]}
    yest_map = {entry["word"]: entry for entry in yest_doc["top_words"]}

    shared_words = set(today_map) & set(yest_map)
    only_today = set(today_map) - set(yest_map)
    only_yesterday = set(yest_map) - set(today_map)

    result = {
        "common": [],
        "new_entries": [],
        "disappeared": []
    }

    for word in shared_words:
        today_rank = today_map[word]["rank"]
        yest_rank = yest_map[word]["rank"]
        change = yest_rank - today_rank
        result["common"].append({
            "word": word,
            "rank_today": today_rank,
            "rank_yesterday": yest_rank,
            "change": change
        })

    for word in only_today:
        result["new_entries"].append({
            "word": word,
            "rank_today": today_map[word]["rank"]
        })

    for word in only_yesterday:
        result["disappeared"].append({
            "word": word,
            "rank_yesterday": yest_map[word]["rank"]
        })

    # Optional: sort common by biggest rank jump
    result["common"].sort(key=lambda x: x["change"], reverse=True)

    return result


def get_word_time_series(word, min_days=7):
    docs = list(find_daily_trends("all", {}))
    data = []

    for doc in docs:
        date = doc["date"]
        for entry in doc["top_words"]:
            if entry["word"] == word:
                data.append({"date": date, "count": entry["count"]})
                break

    df = pd.DataFrame(data)
    if len(df) < min_days:
        return None  # Not enough data yet

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df


if __name__ == "__main__":
    analyze_sample_trends(sample_id="")
