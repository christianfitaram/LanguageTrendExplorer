# services/embeddings.py
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Sequence, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

_CACHE = Path(os.getenv("HF_HOME", os.getenv("TRANSFORMERS_CACHE", "models/transformers"))).resolve()
_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_model: Optional[SentenceTransformer] = None


def get_embedder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME, cache_folder=str(_CACHE))
    return _model


def embed_texts(texts: Sequence[str]) -> np.ndarray:
    """Return L2-normalized float32 embeddings [n, d]."""
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    m = get_embedder()
    X = m.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
    return X.astype("float32")
