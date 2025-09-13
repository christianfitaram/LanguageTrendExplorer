# metadata.py

from __future__ import annotations
import os
from typing import Any, Dict
from lib.repositories.metadata_repository import MetadataRepository
from pymongo.database import Database

repo_metadata = MetadataRepository()

SCORING_DOC_ID = "scoring_v1"

SCORING_DEFAULTS: Dict[str, Any] = {
    "_id": SCORING_DOC_ID,
    "source_weights": {
        "reuters.com": 1.0,
        "apnews.com": 0.98,
        "bbc.com": 0.95,
        "cnn.com": 0.90,
        "unknown": 0.70,
    },
    "category_weights": {
        "general": 1.00,
        "world": 0.95,
        "business": 0.90,
        "technology": 0.80,
        "science": 0.75,
        "health": 0.75,
        "sports": 0.60,
        "entertainment": 0.50,
    },
    "recency_tau_hours": 42,  # τ for time decay
    "link_threshold_cosine": 0.80,  # centroid linking across days
    "ema_lambda": 0.70,  # EMA for momentum
    "novelty_window_days": 7,
    "diversity_bonus_zeta": 0.50,  # multiplier for source diversity
    # Optional model names so the rest of the code can query here:
    "models": {
        "embed": os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "zeroshot": os.getenv("ZEROSHOT_MODEL", "facebook/bart-large-mnli"),
    },
}


def get_scoring_config(db: Database) -> Dict[str, Any]:
    doc = repo_metadata.get_one_metadata({"_id": SCORING_DOC_ID})
    if not doc:
        # Return defaults if not seeded yet
        return SCORING_DEFAULTS
    # Allow env overrides at runtime, e.g., model swaps
    models = doc.get("models", {})
    models["embed"] = os.getenv("EMBED_MODEL", models.get("embed", SCORING_DEFAULTS["models"]["embed"]))
    models["zeroshot"] = os.getenv("ZEROSHOT_MODEL", models.get("zeroshot", SCORING_DEFAULTS["models"]["zeroshot"]))
    doc["models"] = models
    return doc


def seed_scoring_config(db: Database) -> None:
    repo_metadata.update_metadata_upsert(
        {"_id": SCORING_DOC_ID},
        {"$setOnInsert": SCORING_DEFAULTS}
    )
