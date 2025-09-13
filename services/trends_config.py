# services/trends_config.py
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class TrendsConfig:
    # Cosine similarity to *link* a new cluster with an existing thread
    link_threshold_cosine: float = 0.80
    # EMA smoothing for momentum
    ema_lambda: float = 0.70
    # Window (days) to judge novelty of entity sets
    novelty_window_days: int = 7


def default_trends_config() -> TrendsConfig:
    return TrendsConfig()
