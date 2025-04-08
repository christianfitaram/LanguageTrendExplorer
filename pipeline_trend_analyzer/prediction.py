# trend_forecaster.py

from datetime import datetime, timedelta, UTC
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import defaultdict
import numpy as np
import tensorflow as tf
import pandas as pd
import os

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]


# ======================
# Data Preparation
# ======================

def get_word_time_series(word, min_days=7):
    docs = list(db.daily_trends.find({}))
    data = []

    for doc in docs:
        for entry in doc["top_words"]:
            if entry["word"] == word:
                data.append({
                    "date": doc["date"],
                    "count": entry["count"]
                })
                break

    df = pd.DataFrame(data)
    if len(df) < min_days:
        return None

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").set_index("date")
    return df


def prepare_sequences(series, window_size=3):
    X, y = [], []
    for i in range(len(series) - window_size):
        X.append(series[i:i + window_size])
        y.append(series[i + window_size])
    return np.array(X), np.array(y)


# ======================
# Prediction & Training
# ======================

def train_predict(series, window_size=3):
    X, y = prepare_sequences(series, window_size)
    X = X.reshape((X.shape[0], X.shape[1], 1))

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(32, input_shape=(window_size, 1)),
        tf.keras.layers.Dense(1)
    ])

    model.compile(optimizer="adam", loss="mse")
    model.fit(X, y, epochs=100, verbose=0)

    latest_input = series[-window_size:].reshape((1, window_size, 1))
    prediction = model.predict(latest_input, verbose=0)
    return prediction[0][0]


# ======================
# MongoDB Save
# ======================

def save_prediction(word, predicted_count):
    db.trend_predictions.insert_one({
        "word": word,
        "predicted_count": round(float(predicted_count), 2),
        "predicted_for": (datetime.now(UTC) + timedelta(days=1)).date().isoformat(),
        "created_at": datetime.now(UTC)
    })


# ======================
# Main Runner
# ======================

def predict_top_words():
    today = datetime.now(UTC).date().isoformat()
    trend_doc = db.daily_trends.find_one({"date": today})
    if not trend_doc:
        print("No trend data for today.")
        return

    for entry in trend_doc["top_words"][:5]:  # Predict for top 5 words
        word = entry["word"]
        series_df = get_word_time_series(word)
        if series_df is not None:
            y_pred = train_predict(series_df["count"].values)
            save_prediction(word, y_pred)
            print(f"✅ {word}: predicted count for tomorrow = {round(y_pred, 2)}")
        else:
            print(f"⚠️ Not enough data to predict '{word}'")


if __name__ == "__main__":
    predict_top_words()
