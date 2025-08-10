# trend_predictor/pipeline/predict_next_day.py

import pandas as pd
import xgboost as xgb
from datetime import datetime


def predict_for_day(day: str):
    df = pd.read_parquet("data/trend_features.parquet")
    model = xgb.XGBClassifier()
    model.load_model("models/trend_xgb.json")

    # Filter just the rows for the current day
    df_today = df[df["date"] == pd.to_datetime(day)].dropna()
    X = df_today[[c for c in df_today.columns if c not in ["word", "date", "target"] and not c.startswith("topic_")]]
    if "target" in df_today:
        X = X.drop(columns=["target"])

    df_today["probability"] = model.predict_proba(X)[:, 1]
    df_today = df_today[["word", "probability"]].sort_values(by="probability", ascending=False)

    print(f"🔮 Predicted top trending words for {day}:")
    print(df_today.head(15))


if __name__ == "__main__":
    predict_for_day("2025-07-21")
