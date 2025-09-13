# services/scoring.py
from __future__ import annotations
from datetime import datetime, timezone
from math import exp, log
from typing import Dict, Any, Iterable, List
from services.scoring_config import ScoringConfig


def _hours_since(published_at: Any) -> float:
    if not published_at:
        return 72.0
    try:
        # accept either datetime or ISO string
        if isinstance(published_at, str):
            # naive parse for 'YYYY-MM-DDTHH:MM:SSZ'
            return (datetime.now(timezone.utc) - datetime.fromisoformat(
                published_at.replace("Z", "+00:00"))).total_seconds() / 3600.0
        return (datetime.now(timezone.utc) - published_at).total_seconds() / 3600.0
    except Exception:
        return 72.0


def _source_weight(domain: str | None, cfg: ScoringConfig) -> float:
    if not domain:
        return cfg.source_weights.get("unknown", 0.7)
    d = domain.lower()
    # normalize ‘www.’ prefix
    d = d[4:] if d.startswith("www.") else d
    return cfg.source_weights.get(d, cfg.source_weights.get("unknown", 0.7))


def _category_weight(cat: str | None, cfg: ScoringConfig) -> float:
    if not cat:
        return cfg.category_weights.get("general", 1.0)
    return cfg.category_weights.get(cat.lower(), cfg.category_weights.get("general", 1.0))


def _recency_weight(published_at: Any, cfg: ScoringConfig) -> float:
    h = _hours_since(published_at)
    return exp(-h / max(cfg.recency_tau_hours, 1.0))


def article_weight(doc: Dict[str, Any], cfg: ScoringConfig) -> float:
    """
    Lightweight, interpretable weight in [~0.3..1.0+].
    Combines source authority, recency, category. (You can add more factors later.)
    """
    sw = _source_weight(doc.get("source_domain") or doc.get("source"), cfg)
    rw = _recency_weight(doc.get("published_at"), cfg)
    cw = _category_weight(doc.get("category"), cfg)
    # Simple smooth combination
    return 0.5 * sw + 0.3 * rw + 0.2 * cw


def diversity_bonus(sources: Iterable[str], cfg: ScoringConfig) -> float:
    uniq = {(s or "").lower() for s in sources if s}
    if not uniq:
        return 0.0
    reputable = sum(1 for s in uniq if _source_weight(s, cfg) >= 0.9)
    return cfg.diversity_bonus_zeta * log(1.0 + reputable)


def score_cluster(member_docs: List[Dict[str, Any]], cfg: ScoringConfig) -> Dict[str, float]:
    w_sum = sum(article_weight(d, cfg) for d in member_docs)
    srcs = [(d.get("source_domain") or d.get("source") or "").lower() for d in member_docs]
    bonus = diversity_bonus(srcs, cfg)
    return {"sum_article_weight": w_sum, "diversity_bonus": bonus, "cluster_score_today": w_sum + bonus}
