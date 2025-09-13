# app/use_cases/link_threads.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, Iterable, List, Optional, Protocol
import numpy as np

from services.trends_config import TrendsConfig, default_trends_config
from utils.trend_utils import cosine_sim, centroid, jaccard


# ---------- Ports ----------
class CleanArticlesRepo(Protocol):
    def get_articles(self, params: Dict[str, Any], projection: Optional[Dict[str, int]] = None) -> Iterable[
        Dict[str, Any]]: ...


class TrendThreadsRepo(Protocol):
    def get_threads_on(self, date_iso: str) -> Iterable[Dict[str, Any]]: ...

    def get_recent_for_thread(self, thread_id: str, since_iso: str) -> Iterable[Dict[str, Any]]: ...

    def upsert_today(self, selector: Dict[str, Any], doc: Dict[str, Any]) -> None: ...


class DailyTrendsRepo(Protocol):
    def upsert_daily(self, selector: Dict[str, Any], doc: Dict[str, Any]) -> None: ...


# ---------- Types ----------
@dataclass
class LinkThreadsResult:
    sample: str
    date: str
    threads: List[Dict[str, Any]]


# ---------- Use Case ----------
class LinkThreadsUseCase:
    """
    Link today's clusters (with centroids) to prior threads by cosine similarity.
    Compute EMA momentum and novelty (entity Jaccard against last N days).
    """

    def __init__(
            self,
            clean_repo: CleanArticlesRepo,
            threads_repo: TrendThreadsRepo,
            daily_repo: DailyTrendsRepo,
            cfg: Optional[TrendsConfig] = None,
    ) -> None:
        self.clean_repo = clean_repo
        self.threads_repo = threads_repo
        self.daily_repo = daily_repo
        self.cfg = cfg or default_trends_config()

    def _link_target(self, today_centroid: np.ndarray, prev_threads: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        best: Optional[Dict[str, Any]] = None
        best_sim: float = -1.0
        for t in prev_threads:
            c_prev = np.array(t.get("centroid") or [], dtype="float32")
            if c_prev.size == 0:
                continue
            sim = cosine_sim(today_centroid, c_prev)
            if sim > best_sim:
                best_sim, best = sim, t
        if best and best_sim >= self.cfg.link_threshold_cosine:
            return best
        return None

    def _compute_ema(self, today_score: float, prev_ema: Optional[float]) -> float:
        lam = self.cfg.ema_lambda
        if prev_ema is None:
            return today_score
        return lam * today_score + (1.0 - lam) * prev_ema

    def _compute_novelty(self, today_entities: List[str], thread_id: Optional[str], today_iso: str) -> float:
        if not thread_id:
            # brand new thread is maximally novel
            return 1.0
        # Lookback window
        since = (datetime.fromisoformat(today_iso).date() - timedelta(days=self.cfg.novelty_window_days)).isoformat()
        hist = list(self.threads_repo.get_recent_for_thread(thread_id, since))
        hist_ents: List[str] = []
        for h in hist:
            hist_ents.extend(h.get("top_entities") or [])
        overlap = jaccard(today_entities, hist_ents)
        return max(0.0, 1.0 - overlap)

    def run(
            self,
            sample_id: str,
            date_iso: Optional[str],
            ranked_clusters: List[Dict[str, Any]],
    ) -> LinkThreadsResult:
        today = date_iso or datetime.now(UTC).date().isoformat()

        # Gather yesterday threads to link against
        prev_threads = list(self.threads_repo.get_threads_on(
            (datetime.fromisoformat(today) - timedelta(days=1)).date().isoformat()
        ))

        out: List[Dict[str, Any]] = []
        for c in ranked_clusters:
            # centroid
            c_vec = np.array(c.get("centroid") or [], dtype="float32")
            # link candidate
            linked = self._link_target(c_vec, prev_threads)
            if linked:
                thread_id = linked["thread_id"]
                prev_ema = linked.get("ema")
            else:
                thread_id = f"thr-{c['cluster_id']}"  # simple deterministic new id
                prev_ema = None

            # score today (already in c)
            score_today = float(c.get("cluster_score_today", 0.0))
            ema = self._compute_ema(score_today, prev_ema)
            novelty = self._compute_novelty(c.get("top_entities") or [], thread_id if linked else None, today)

            thread_doc = {
                "date": today,
                "sample": sample_id,
                "thread_id": thread_id,
                "cluster_id": c["cluster_id"],
                "size": c["size"],
                "centroid": (c_vec / (np.linalg.norm(c_vec) + 1e-9)).tolist() if c_vec.size else [],
                "topic_label": c.get("topic_label"),
                "top_terms": c.get("top_terms") or [],
                "top_entities": c.get("top_entities") or [],
                "sources": c.get("sources") or [],
                "score_components": c.get("score_components") or {},
                "cluster_score_today": score_today,
                "ema": ema,
                "novelty": novelty,
                "trend_score": ema + novelty + float(c.get("score_components", {}).get("diversity_bonus", 0.0)),
                "created_at": datetime.now(UTC),
            }
            # Persist/Upsert per (date, thread_id)
            self.threads_repo.upsert_today(
                {"date": today, "thread_id": thread_id},
                thread_doc,
            )
            # Also upsert a daily_trends view if you prefer one doc per (date, thread_id)
            self.daily_repo.upsert_daily(
                {"date": today, "thread_id": thread_id},
                {
                    "date": today,
                    "thread_id": thread_id,
                    "sample": sample_id,
                    "trend_score": thread_doc["trend_score"],
                    "EMA": ema,
                    "novelty": novelty,
                    "topic_label": c.get("topic_label"),
                    "top_entities": c.get("top_entities") or [],
                    "top_terms": c.get("top_terms") or [],
                    "size": c["size"],
                    "representative_titles": c.get("representative_titles") or [],
                    "sources": c.get("sources") or [],
                    "cluster_id": c["cluster_id"],
                    "centroid": thread_doc["centroid"],
                    "created_at": thread_doc["created_at"],
                },
            )
            out.append(thread_doc)

        # Sort by final trend score (EMA + novelty + diversity bonus)
        out.sort(key=lambda d: d["trend_score"], reverse=True)
        return LinkThreadsResult(sample=sample_id, date=today, threads=out)
