#!/usr/bin/env python3
"""
Download all models your pipeline needs into the local cache (offline-ready).
"""

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
)

CACHE_DIR = "./models/transformers"

def dl_sentiment():
    name = "distilbert-base-uncased-finetuned-sst-2-english"
    print(f"⬇️ {name}")
    AutoTokenizer.from_pretrained(name, cache_dir=CACHE_DIR)
    AutoModelForSequenceClassification.from_pretrained(name, cache_dir=CACHE_DIR)

def dl_topic():
    name = "facebook/bart-large-mnli"
    print(f"⬇️ {name}")
    AutoTokenizer.from_pretrained(name, cache_dir=CACHE_DIR)
    AutoModelForSequenceClassification.from_pretrained(name, cache_dir=CACHE_DIR)

def dl_summarizer():
    name = "facebook/bart-large-cnn"
    print(f"⬇️ {name}")
    AutoTokenizer.from_pretrained(name, cache_dir=CACHE_DIR)
    AutoModelForSeq2SeqLM.from_pretrained(name, cache_dir=CACHE_DIR)

def main():
    dl_sentiment()
    dl_topic()
    dl_summarizer()
    print("✅ All models cached.")

if __name__ == "__main__":
    main()
