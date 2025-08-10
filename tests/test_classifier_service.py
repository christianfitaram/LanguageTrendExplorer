# tests/test_classifier_service.py
from datetime import datetime, timezone
from services.classifier_service import ClassifierService, ArticleIn


class FakePipelines:
    def __init__(self):
        self.topic_calls = []
        self.sent_calls = []

    def topic(self, text: str):
        self.topic_calls.append(text)
        # mimic zero-shot output
        return {"labels": ["technology and innovation", "business and finance"], "scores": [0.88, 0.12]}

    def sentiment(self, text: str):
        self.sent_calls.append(text)
        # mimic sentiment-analysis output
        return {"label": "POSITIVE", "score": 0.97}


def test_classify_minimal_happy_path():
    pipes = FakePipelines()
    svc = ClassifierService(pipelines=pipes, candidate_topics=[
        "technology and innovation", "business and finance", "politics and government"
    ])

    art = ArticleIn(
        title="New AI chip launches",
        url="https://example.com/ai-chip",
        text="A short body of text about a new AI chip.",
        source="example-source",
        scraped_at=datetime.now(timezone.utc),
    )

    out = svc.classify(art=art, batch=3, sample="7-2025-08-10")

    assert out.title == art.title
    assert out.url == art.url
    assert out.text == art.text  # should keep the original text on output
    assert out.source == art.source
    assert out.batch == 3
    assert out.sample == "7-2025-08-10"

    # topic/sentiment present and in expected shape
    assert out.topic == "technology and innovation"
    assert isinstance(out.sentiment, dict)
    assert out.sentiment.get("label") == "POSITIVE"
    assert isinstance(out.sentiment.get("score"), float)

    # pipes were actually called
    assert len(pipes.topic_calls) == 1
    assert len(pipes.sent_calls) == 1


def test_classify_long_text_does_not_crash():
    pipes = FakePipelines()
    svc = ClassifierService(pipelines=pipes, candidate_topics=["technology and innovation"])

    long_text = "lorem ipsum " * 5000  # very long
    art = ArticleIn(
        title=None,
        url="https://example.com/long",
        text=long_text,
        source=None,
        scraped_at=datetime.now(timezone.utc),
    )

    out = svc.classify(art=art, batch=1, sample="1-2025-08-10")

    # output still well-formed
    assert out.url.endswith("/long")
    assert out.batch == 1
    assert out.sample == "1-2025-08-10"
    assert "label" in out.sentiment
    assert out.topic in {"technology and innovation", "unknown"}
