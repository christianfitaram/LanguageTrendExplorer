# services/labeling.py
from __future__ import annotations
from typing import Dict, List, Tuple
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


def tfidf_top_terms(texts: List[str], k: int = 8) -> List[str]:
    if not texts:
        return []
    vect = TfidfVectorizer(
        stop_words="english",
        max_df=0.9,
        min_df=1,
        ngram_range=(1, 2),
        norm="l2",
    )
    X = vect.fit_transform(texts)
    scores = np.asarray(X.mean(axis=0)).ravel()
    idx = scores.argsort()[::-1][:k]
    inv_vocab = {v: k for k, v in vect.vocabulary_.items()}
    return [inv_vocab[i] for i in idx]


def label_from_terms_entities_topics(
        summaries: List[str],
        entities_lists: List[List[str]],
        topics: List[str],
        top_terms_k: int = 8,
        top_entities_k: int = 6,
) -> Tuple[str, List[str], List[str], Dict[str, int]]:
    terms = tfidf_top_terms(summaries, k=top_terms_k)
    ent_counter: Counter[str] = Counter()
    for ents in entities_lists:
        ent_counter.update([e.lower() for e in (ents or [])])

    top_entities = [w for w, _ in ent_counter.most_common(top_entities_k)]
    topic_counter = Counter([t for t in topics if t and t.lower() != "unknown"])

    # Build a concise label (fallbacks in order)
    pieces: List[str] = []
    if topic_counter:
        pieces.append(topic_counter.most_common(1)[0][0])
    if top_entities[:2]:
        pieces.extend(top_entities[:2])
    elif terms[:2]:
        pieces.extend(terms[:2])

    label = " – ".join(pieces) if pieces else (terms[0] if terms else "misc")
    return label, terms, top_entities, dict(topic_counter)
