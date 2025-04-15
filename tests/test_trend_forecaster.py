from unittest.mock import MagicMock
import pandas as pd
from pipeline_trend_analyzer.prediction import build_model, reset_model_weights, prepare_sequences, \
    get_word_time_series, save_prediction
import numpy as np


def test_prepare_sequences_basic():
    data = [1, 2, 3, 4, 5]
    X, y = prepare_sequences(data, window_size=3)
    assert (X == [[1, 2, 3], [2, 3, 4]]).all()
    assert (y == [4, 5]).all()


def test_get_word_time_series_enough_samples(monkeypatch):
    mock_repo = MagicMock()
    mock_repo.get_daily_trends.return_value = [
        {"sample": "1-2025-04-10", "top_words": [{"word": "ai", "count": 10}]},
        {"sample": "1-2025-04-11", "top_words": [{"word": "ai", "count": 15}]},
        {"sample": "1-2025-04-12", "top_words": [{"word": "ai", "count": 20}]},
    ]
    monkeypatch.setattr("pipeline_trend_analyzer.prediction.repo_daily_trends", mock_repo)
    df = get_word_time_series("ai", min_samples=2)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert df.iloc[0]["count"] == 10


def test_reset_model_weights():
    model = build_model(window_size=3)
    original_weights = model.get_weights()

    # Alter weights
    model.set_weights([w + np.random.rand(*w.shape) for w in original_weights])

    reset_fn = reset_model_weights(model)
    reset_fn()
    reset_weights = model.get_weights()

    for ow, rw in zip(original_weights, reset_weights):
        assert np.allclose(ow, rw)


def test_save_prediction(monkeypatch):
    mock_repo = MagicMock()
    monkeypatch.setattr("pipeline_trend_analyzer.prediction.repo_trend_predictions", mock_repo)
    save_prediction("ai", 42.5)
    args = mock_repo.insert_trend_prediction.call_args[0][0]
    assert args["word"] == "ai"
    assert args["predicted_count"] == 42.5
    assert "predicted_for" in args
