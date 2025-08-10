# tests/test_summarizer.py
import importlib
import sys
import types
import pytest

@pytest.fixture
def summarizer_module(monkeypatch):
    """
    Patch heavy HF objects BEFORE importing pipeline_sample.summarizer, and force a fresh import.
    This stops real model/tokenizer loading and ensures the module uses our fakes.
    """
    # 1) Fake pipeline that "summarizes" by truncating text and records calls
    calls = {"inputs": []}

    class FakeSummarizer:
        def __call__(self, text, max_length=None, min_length=None, do_sample=None, **kwargs):
            calls["inputs"].append(text)
            if isinstance(text, str):
                return [{"summary_text": text[: (max_length or 200)]}]
            joined = " ".join(map(str, text))
            return [{"summary_text": joined[: (max_length or 200)]}]

    def fake_pipeline(task, model=None, tokenizer=None, device=None, **kwargs):
        return FakeSummarizer()

    # 2) Fake tokenizer with a cheap encode() to exercise chunking logic
    class FakeTokenizer:
        def encode(self, text, add_special_tokens=False):
            # Approximate token count by whitespace splitting
            return text.split()

    class FakeBartTokenizer:
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            return FakeTokenizer()

    # 3) Apply patches BEFORE import
    import transformers
    monkeypatch.setattr(transformers, "pipeline", fake_pipeline, raising=True)
    monkeypatch.setattr(transformers, "BartTokenizer", FakeBartTokenizer, raising=True)

    # Optional: mute MPS to avoid device noise
    import torch
    monkeypatch.setattr(torch.backends.mps, "is_available", lambda: False, raising=True)
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False, raising=True)

    # 4) Force a fresh import of the module so it picks up our fakes
    sys.modules.pop("pipeline_sample.summarizer", None)
    mod = importlib.import_module("pipeline_sample.summarizer")

    # Safety: ensure the module's 'pipeline' name is our fake too
    monkeypatch.setattr(mod, "pipeline", fake_pipeline, raising=True)

    # Expose call log
    mod.__test_calls__ = calls
    return mod


def test_short_text_returns_original(summarizer_module):
    text = "Short article body."
    out = summarizer_module.smart_summarize(text)
    assert out == text
    assert summarizer_module.__test_calls__["inputs"] == []  # no pipeline call


def test_long_text_is_summarized_and_shorter(summarizer_module):
    long_text = "Sentence. " * 2000
    out = summarizer_module.smart_summarize(long_text)

    assert isinstance(out, str)
    assert out.strip() != ""
    assert len(out) < len(long_text)

    # pipeline was invoked at least once
    assert len(summarizer_module.__test_calls__["inputs"]) >= 1


def test_chunking_triggers_multiple_calls_when_needed(summarizer_module):
    text = ("This is a fairly normal sentence used for building a long document. " * 600).strip()
    _ = summarizer_module.smart_summarize(text)

    calls = summarizer_module.__test_calls__["inputs"]
    assert len(calls) >= 2, f"Expected multiple chunks, got {len(calls)}"
