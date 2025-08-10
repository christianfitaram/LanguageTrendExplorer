# services/daily_trends.py
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, TypedDict


class DistributionItem(TypedDict):
    label: str
    percentage: int


class RankedWord(TypedDict):
    word: str
    count: int
    rank: int
    context: Dict[str, List[DistributionItem]]


@dataclass(frozen=True)
class WordOccurrence:
    word: str
    topic: Optional[str]
    sentiment: Optional[str]


class DailyTrendsService:
    """
    Pure application service:
    - input: list of cleaned article dicts
    - output: ranked words + simple metrics (no I/O, no DB)
    """

    def extract_occurrences(self, articles: List[Dict[str, Any]]) -> List[WordOccurrence]:
        out: List[WordOccurrence] = []
        for a in articles:
            topic = (a.get("topic") or "").strip().lower()
            sentiment = (a.get("sentiment", {}).get("label") or "").strip().lower()
            nouns = a.get("nouns", []) or []

            valid_topic = topic not in {"", "topic", "unknown", "none"}
            valid_sent = sentiment not in {"", "n/a", "label", "unknown", "none"}

            tval = topic if valid_topic else None
            sval = sentiment if valid_sent else None

            for noun in nouns:
                out.append(WordOccurrence(word=noun, topic=tval, sentiment=sval))
        return out

    def build_counter(self, occurrences: List[WordOccurrence]) -> Counter:
        return Counter(w.word for w in occurrences)

    def top_n(self, counter: Counter, n: int) -> List[tuple[str, int]]:
        return counter.most_common(n)

    def group_context(self, occurrences: List[WordOccurrence]) -> tuple[dict[str, List[str]], dict[str, List[str]]]:
        topics: dict[str, List[str]] = defaultdict(list)
        sentiments: dict[str, List[str]] = defaultdict(list)
        for w in occurrences:
            if w.topic:
                topics[w.word].append(w.topic)
            if w.sentiment:
                sentiments[w.word].append(w.sentiment)
        return topics, sentiments

    @staticmethod
    def distribution(values: List[str]) -> List[DistributionItem]:
        if not values:
            return []
        c = Counter(values)
        total = sum(c.values()) or 1
        return [{"label": k, "percentage": round((v / total) * 100)} for k, v in c.most_common()]

    def build_ranked_words(
        self,
        top_words: List[tuple[str, int]],
        occurrences: List[WordOccurrence],
    ) -> List[RankedWord]:
        topics_by_word, sentiments_by_word = self.group_context(occurrences)
        ranked: List[RankedWord] = []
        for idx, (word, count) in enumerate(top_words):
            ranked.append({
                "word": word,
                "count": count,
                "rank": idx + 1,
                "context": {
                    "topics": self.distribution(topics_by_word.get(word, [])),
                    "sentiments": self.distribution(sentiments_by_word.get(word, [])),
                },
            })
        return ranked

    def compute(self, articles: List[Dict[str, Any]], limit: int = 15) -> Dict[str, Any]:
        """
        Returns a pure result dict:
        {
          "metrics": {"total_words": int, "distinct_words": int},
          "ranked_words": [RankedWord, ...]
        }
        """
        occurrences = self.extract_occurrences(articles)
        counter = self.build_counter(occurrences)
        metrics = {
            "total_words": sum(counter.values()),
            "distinct_words": len(counter),
        }
        top_words = self.top_n(counter, limit)
        ranked_words = self.build_ranked_words(top_words, occurrences)
        return {"metrics": metrics, "ranked_words": ranked_words}
