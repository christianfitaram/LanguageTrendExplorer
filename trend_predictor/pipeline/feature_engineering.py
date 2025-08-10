# trend_predictor/pipeline/feature_engineering.py

import os
import pandas as pd
from tqdm import tqdm
from datetime import datetime

from mongo.mongodb_client import db
from mongo.repositories.repository_daily_trends import RepositoryDailyTrends

trends = RepositoryDailyTrends(db)


def build_daily_noun_stats(start_date: str, end_date: str):
    """
    Constructs a DataFrame where each row is (noun, date) with its count, rank, sentiment, and topic context.
    """
    date_range = pd.date_range(start=start_date, end=end_date)
    rows = []

    for date in tqdm(date_range):
        query_date = date.strftime("%Y-%m-%d")
        doc = trends.get_one_daily_trends({"date": query_date})

        if not doc:
            print(f"❌ No document for {query_date}")
            continue

        print(f"✅ Found doc for {query_date} — keys: {list(doc.keys())}")

        top_words = doc.get("top_words", [])
        for entry in top_words:
            word = entry["word"]
            print(word)
            count = entry["count"]
            rank = entry["rank"]
            topics = entry.get("contexto", {}).get("topics", [])
            sentiments = entry.get("contexto", {}).get("sentiments", [])

            # FIXED topic distribution
            topic_labels = [t.get("label") for t in topics if isinstance(t, dict)]
            topic_dist = {
                label: topic_labels.count(label) / len(topic_labels)
                for label in set(topic_labels)
            } if topic_labels else {}

            # sentiment average
            sentiment_score = (
                sum(s.get("score", 0) for s in sentiments if isinstance(s, dict)) / len(sentiments)
                if sentiments else 0
            )

            row = {
                "word": word,
                "date": date,
                "count": count,
                "rank": rank,
                "sentiment_score": sentiment_score,
                **{f"topic_{k}": v for k, v in topic_dist.items()}
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    return df


def add_time_series_features(df):
    if df.empty:
        print("❌ DataFrame is empty, skipping feature engineering.")
        return df

    df = df.dropna(subset=["word", "date"])
    df = df.sort_values(["word", "date"])

    # Rolling features
    df["count_avg_3d"] = df.groupby("word")["count"].rolling(window=3, min_periods=1).mean().reset_index(level=0,
                                                                                                         drop=True)
    df["count_avg_7d"] = df.groupby("word")["count"].rolling(window=7, min_periods=1).mean().reset_index(level=0,
                                                                                                         drop=True)
    df["sentiment_avg_7d"] = df.groupby("word")["sentiment_score"].rolling(window=7, min_periods=1).mean().reset_index(
        level=0, drop=True)

    # Rank delta (today - yesterday)
    df["rank_delta"] = df.groupby("word")["rank"].diff()

    # Date features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month

    return df


def create_targets(df: pd.DataFrame):
    """
    Adds a binary target: 1 if the word is in top 15 the next day, 0 otherwise.
    """
    df["next_date"] = df["date"] + pd.Timedelta(days=1)

    top15_by_day = df[df["rank"] <= 15][["word", "date"]].copy()
    top15_by_day["in_top15"] = 1

    df = df.merge(
        top15_by_day.rename(columns={"date": "next_date", "in_top15": "target"}),
        on=["word", "next_date"],
        how="left"
    )
    df["target"] = df["target"].fillna(0).astype(int)
    return df.drop(columns=["next_date"])


def save_features():
    df = build_daily_noun_stats("2025-07-13", "2025-07-20")
    df = add_time_series_features(df)
    df = create_targets(df)

    output_path = os.path.join(os.path.dirname(__file__), "..", "data")
    output_path = os.path.abspath(output_path)

    os.makedirs(output_path, exist_ok=True)
    df.to_parquet(os.path.join(output_path, "trend_features.parquet"))
    print("✅ Feature dataset saved!")


if __name__ == "__main__":
    save_features()
