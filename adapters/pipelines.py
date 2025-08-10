# adapters/pipelines.py
from __future__ import annotations
from typing import Dict, Any, List


class HFPipelines:
    def __init__(self, sentiment_pipe, zero_shot_pipe, candidate_labels: List[str]) -> None:
        self._sent = sentiment_pipe
        self._zs = zero_shot_pipe
        self._labels = candidate_labels

    def sentiment(self, text: str) -> Dict[str, Any]:
        return self._sent(text)[0]

    def topic(self, text: str) -> Dict[str, Any]:
        return self._zs(text, candidate_labels=self._labels)
