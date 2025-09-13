# app/use_cases/rank_clusters.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Protocol
from services.scoring_config import ScoringConfig, default_scoring_config
from services.scoring import score_cluster


class CleanArticlesRepo(Protocol):
    def get_articles(self, params: Dict[str, Any], projection: Optional[Dict[str, int]] = None) -> Iterable[
        Dict[str, Any]]: ...


@dataclass
class RankClustersResult:
    sample: str
    clusters: List[Dict[str, Any]]


class RankClustersUseCase:
    def __init__(self, clean_repo: CleanArticlesRepo, cfg: Optional[ScoringConfig] = None) -> None:
        self.clean_repo = clean_repo
        self.cfg = cfg or default_scoring_config()

    def run(self, sample_id: str, clusters: List[Dict[str, Any]]) -> RankClustersResult:
        # Pull only what scoring needs
        proj = {"_id": 1, "source": 1, "source_domain": 1, "published_at": 1, "category": 1}
        docs_by_id = {d["_id"]: d for d in self.clean_repo.get_articles({"sample": sample_id}, projection=proj)}

        ranked: List[Dict[str, Any]] = []
        for c in clusters:
            ids = c.get("member_ids") or []
            members = [docs_by_id.get(_id) for _id in ids]
            members = [m for m in members if m]  # drop missing
            sc = score_cluster(members, self.cfg)

            ranked.append({
                **c,
                "score_components": sc,
                "cluster_score_today": sc["cluster_score_today"],
            })

        ranked.sort(key=lambda r: r["cluster_score_today"], reverse=True)
        return RankClustersResult(sample=sample_id, clusters=ranked)
