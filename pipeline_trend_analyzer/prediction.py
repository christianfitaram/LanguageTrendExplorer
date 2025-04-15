# trend_forecaster.py
import argparse
from datetime import datetime, timedelta, UTC
import numpy as np
import tensorflow as tf
import pandas as pd
from mongo.mongodb_client import db
from mongo.repositories.repository_daily_trends import RepositoryDailyTrends
from mongo.repositories.repository_trend_predictions import RepositoryTrendPredictions
from utils.utils_functions import is_valid_sample

repo_daily_trends = RepositoryDailyTrends(db)
repo_trend_predictions = RepositoryTrendPredictions(db)


def build_model(window_size):
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(window_size, 1)),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def reset_model_weights(model):
    initial_weights = model.get_weights()

    def reset():
        model.set_weights(initial_weights)

    return reset


def get_word_time_series(word, min_samples=3):
    docs = list(repo_daily_trends.get_daily_trends({}))
    data = []

    for doc in docs:
        if "top_words" not in doc or "sample" not in doc:
            continue

        for entry in doc["top_words"]:
            if entry["word"] == word:
                data.append({
                    "date": doc["created_at"],  # already datetime
                    "count": entry["count"]
                })
                break

    df = pd.DataFrame(data)
    if len(df) < min_samples:
        return None

    df["date"] = pd.to_datetime(df["date"])  # ✅ no .str needed
    df = df.sort_values("date").set_index("date")
    return df


def prepare_sequences(series, window_size=3):
    X, y = [], []
    for i in range(len(series) - window_size):
        X.append(series[i:i + window_size])
        y.append(series[i + window_size])
    return np.array(X), np.array(y)


def save_prediction(word, predicted_count):
    repo_trend_predictions.insert_trend_prediction({
        "word": word,
        "predicted_count": round(predicted_count.item(), 2),
        "predicted_for": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(),
        "created_at": datetime.now(UTC)
    })


def predict_top_words(sample_id: str = None):
    if sample_id is None:
        sample = input("Enter the sample string (e.g. '1-2025-04-12'): ")
        while is_valid_sample(sample) is False:
            sample = input("Incorrect format (e.g. '1-2025-04-12'): ")

    window_size = 3
    model = build_model(window_size)
    reset_weights = reset_model_weights(model)

    trend_doc = repo_daily_trends.get_one_daily_trends({"sample": sample_id})
    if not trend_doc:
        print(f"No trend data for sample '{sample_id}'")
        return

    for entry in trend_doc["top_words"][:5]:
        word = entry["word"]
        series_df = get_word_time_series(word)
        if series_df is not None:
            if len(series_df) <= window_size:
                print(f"⚠️ Not enough data points for '{word}' (need > {window_size}, got {len(series_df)})")
                continue

            X, y = prepare_sequences(series_df["count"].values, window_size)
            if len(X) == 0:
                print(f"⚠️ Could not generate sequences for '{word}'")
                continue

            X = X.reshape((X.shape[0], X.shape[1], 1))

            reset_weights()
            model.fit(X, y, epochs=100, verbose=0)

            latest_input = series_df["count"].values[-window_size:].reshape((1, window_size, 1))
            y_pred = model.predict(latest_input, verbose=0)

            save_prediction(word, y_pred)
            print(f"✅ {word}: predicted count for next sample = {round(y_pred[0][0], 2)}")


if __name__ == "__main__":
    predict_top_words()
