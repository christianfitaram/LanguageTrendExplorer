# services/scoring_config.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ScoringConfig:
    source_weights: Dict[str, float] = field(default_factory=lambda: {
        "reuters.com": 1.00, "apnews.com": 0.98, "bbc.com": 0.95, "cnn.com": 0.90, "unknown": 0.70
    })
    category_weights: Dict[str, float] = field(default_factory=lambda: {
        "general": 1.00, "world": 0.95, "business": 0.90, "technology": 0.80,
        "science": 0.75, "health": 0.75, "sports": 0.60, "entertainment": 0.50
    })
    recency_tau_hours: float = 42.0  # time decay τ
    diversity_bonus_zeta: float = 0.5  # multiplier for source diversity


def default_scoring_config() -> ScoringConfig:
    return ScoringConfig()
