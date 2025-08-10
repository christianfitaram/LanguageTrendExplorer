#!/usr/bin/env python3
"""
Verify that all required Hugging Face models for the pipeline
are available locally and can be loaded offline.

Usage:
    python scripts/check_models.py
"""

import os
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    BartTokenizer,
    pipeline
)


def main():
    # Resolve cache path from env or default
    cache = Path(os.getenv("HF_HOME", os.getenv("TRANSFORMERS_CACHE", "models/transformers"))).resolve()
    print(f"📦 Using HF cache: {cache}")

    # Force offline
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    # ---- Sentiment model (DistilBERT) ----
    print("\n🔍 Checking sentiment model (distilbert-base-uncased-finetuned-sst-2-english)...")
    tok = AutoTokenizer.from_pretrained(
        "distilbert-base-uncased-finetuned-sst-2-english",
        cache_dir=str(cache),
        local_files_only=True
    )
    mdl = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-uncased-finetuned-sst-2-english",
        cache_dir=str(cache),
        local_files_only=True
    )
    p = pipeline("sentiment-analysis", model=mdl, tokenizer=tok)
    print("✅ Sentiment model loaded. Test run:", p("quick smoke test"))

    # ---- Topic model (BART MNLI) ----
    print("\n🔍 Checking topic classification model (facebook/bart-large-mnli)...")
    AutoTokenizer.from_pretrained(
        "facebook/bart-large-mnli",
        cache_dir=str(cache),
        local_files_only=True
    )
    AutoModelForSequenceClassification.from_pretrained(
        "facebook/bart-large-mnli",
        cache_dir=str(cache),
        local_files_only=True
    )
    print("✅ Topic model loaded.")

    # ---- Summarizer model (BART CNN) ----
    print("\n🔍 Checking summarizer model (facebook/bart-large-cnn)...")
    bart_tok = BartTokenizer.from_pretrained(
        "facebook/bart-large-cnn",
        cache_dir=str(cache),
        local_files_only=True
    )
    from transformers import AutoModelForSeq2SeqLM
    bart_model = AutoModelForSeq2SeqLM.from_pretrained(
        "facebook/bart-large-cnn",
        cache_dir=str(cache),
        local_files_only=True
    )
    _summarizer = pipeline(
        "summarization",
        model=bart_model,
        tokenizer=bart_tok
    )
    print("✅ Summarizer loaded. Test run:",
          _summarizer("This is a very short sentence about AI.",
                      max_length=10, min_length=5, do_sample=False))
    print("\n🎉 All models available offline.")


if __name__ == "__main__":
    main()
