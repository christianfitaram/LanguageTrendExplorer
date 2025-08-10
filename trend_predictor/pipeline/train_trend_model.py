# trend_predictor/pipeline/train_trend_model.py
import os
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def train_model():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    feature_path = os.path.join(base_dir, "data", "trend_features.parquet")
    model_output_path = os.path.join(base_dir, "models", "trend_xgb.json")

    df = pd.read_parquet(feature_path)
    # Drop missing values
    df = df.dropna()

    feature_cols = [
                       "count", "rank", "count_avg_3d", "count_avg_7d", "sentiment_score",
                       "sentiment_avg_7d", "rank_delta", "day_of_week", "month"
                   ] + [c for c in df.columns if c.startswith("topic_")]

    X = df[feature_cols]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, test_size=0.2, random_state=42)

    model = xgb.XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred))

    model.save_model("models/trend_xgb.json")
    print("✅ Model trained and saved!")


if __name__ == "__main__":
    train_model()
