# app/use_cases/build_daily_clusters.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Dict, Iterable, List, Optional, Protocol

import numpy as np

from services.embeddings import embed_texts
from services.clusterer import cluster_embeddings
from services.labeling import label_from_terms_entities_topics


# ---- Ports ----
class CleanArticlesRepo(Protocol):
    def get_articles_broad(self, filter_param: Dict[str, Any], projection_param: Optional[Dict[str, int]] = None): ...
    def update_articles(self, selector: Dict[str, Any], update: Dict[str, Any]) -> int: ...


@dataclass
class BuildDailyClustersConfig:
    cosine_threshold: float = 0.30
    min_cluster_size: int = 3


class BuildDailyClustersUseCase:
    def __init__(self, clean_repo: CleanArticlesRepo, config: Optional[BuildDailyClustersConfig] = None) -> None:
        self.clean_repo = clean_repo
        self.cfg = config or BuildDailyClustersConfig()

    def run(self, sample_id: str) -> Dict[str, Any]:
        # Pull needed fields only
        proj = {
            "_id": 1, "title": 1, "url": 1, "summary": 1, "text": 1, "nouns": 1,
            "embedding": 1, "topic": 1, "sentiment": 1, "source": 1, "source_domain": 1, "published_at": 1
        }
        docs = list(self.clean_repo.get_articles_broad({"sample": sample_id}, proj))
        if not docs:
            return {"sample": sample_id, "clusters": [], "meta": {"count": 0}}

        # 1) choose text for vectorization (prefer summary)
        texts = [(d.get("summary") or d.get("text") or "").strip() for d in docs]
        # 2) use stored embeddings if present and valid; otherwise compute
        stored = [d.get("embedding") for d in docs]
        if any(v is None or not isinstance(v, list) or len(v) < 10 for v in stored):
            X = embed_texts(texts)
        else:
            X = np.array(stored, dtype="float32")
            # normalize to unit length if not already
            norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
            X = (X / norms).astype("float32")

        # 3) cluster
        labels, _ = cluster_embeddings(
            X,
            cosine_threshold=self.cfg.cosine_threshold,
            min_cluster_size=self.cfg.min_cluster_size,
        )

        # group by cluster id
        by_c: Dict[int, List[int]] = {}
        for idx, c in enumerate(labels):
            by_c.setdefault(int(c), []).append(idx)

        clusters: List[Dict[str, Any]] = []
        now = datetime.now(UTC)
        order = 0
        for cid, idxs in by_c.items():
            if cid == -1:
                continue  # treat as noise
            items = [docs[i] for i in idxs]
            titles = [it.get("title") for it in items if it.get("title")]
            sources = [it.get("source_domain") or it.get("source") for it in items]
            topics = [it.get("topic") for it in items]
            entities = [it.get("nouns") or [] for it in items]
            sums = [texts[i] for i in idxs]

            label, top_terms, top_entities, topic_dist = label_from_terms_entities_topics(
                sums, entities, topics
            )

            clusters.append({
                "cluster_id": f"{sample_id}-{order}",
                "size": len(items),
                "topic_label": label,
                "top_terms": top_terms,
                "top_entities": top_entities,
                "topic_distribution": topic_dist,
                "representative_titles": titles[:6],
                "sources": [{"domain": s, "count": sources.count(s)} for s in sorted(set(sources or []))],
                "created_at": now,
            })
            order += 1

        # sort by size desc as a first proxy (Phase 3 will compute proper scores)
        clusters.sort(key=lambda c: c["size"], reverse=True)
        return {"sample": sample_id, "clusters": clusters, "meta": {"count": len(docs)}}
