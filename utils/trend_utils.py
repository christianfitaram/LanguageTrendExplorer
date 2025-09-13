# services/trend_utils.py
from __future__ import annotations
from typing import Iterable, List, Set
import numpy as np


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


def centroid(vectors: np.ndarray) -> np.ndarray:
    if len(vectors) == 0:
        return np.zeros((0,), dtype="float32")
    c = vectors.mean(axis=0)
    n = np.linalg.norm(c) + 1e-9
    return (c / n).astype("float32")


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    A: Set[str] = set([x.lower() for x in a if x])
    B: Set[str] = set([x.lower() for x in b if x])
    if not A and not B:
        return 0.0
    return len(A & B) / float(len(A | B))
