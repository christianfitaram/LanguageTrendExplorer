# services/clusterer.py
from __future__ import annotations
from typing import Tuple
import numpy as np
from sklearn.cluster import AgglomerativeClustering


def cluster_embeddings(
        X: np.ndarray,
        cosine_threshold: float = 0.30,  # lower = looser clusters; tune 0.25–0.35
        min_cluster_size: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Returns (labels, centroids). Noise points (singletons) get -1.
    """
    if len(X) == 0:
        return np.array([], dtype=int), np.zeros((0, X.shape[1]), dtype=X.dtype)

    # Agglomerative supports metric='cosine' with linkage='average'
    # Use distance_threshold mapping from cosine sim: dist = 1 - sim
    dist_threshold = max(1e-6, cosine_threshold)  # treat as distance directly
    model = AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=dist_threshold,
    )
    labels = model.fit_predict(X)

    # Drop tiny clusters to noise = -1
    final = labels.copy()
    if len(final):
        for lbl in set(final.tolist()):
            if lbl == -1:
                continue
            size = int((final == lbl).sum())
            if size < min_cluster_size:
                final[final == lbl] = -1

    # Compute centroids for non-noise clusters
    uniq = sorted([c for c in set(final.tolist()) if c != -1])
    centroids = []
    for c in uniq:
        centroids.append(X[final == c].mean(axis=0))
    return final, np.vstack(centroids) if centroids else np.zeros((0, X.shape[1]), dtype=X.dtype)
