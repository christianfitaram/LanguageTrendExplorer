#!/usr/bin/env python3
"""
Download the facebook/bart-large-cnn model and tokenizer into the local cache
so it can be used offline by the summarizer.
"""

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


def main():
    model_name = "facebook/bart-large-cnn"
    cache_dir = "./models/transformers"

    print(f"⬇️ Downloading {model_name} to {cache_dir}...")
    AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=cache_dir)
    print("✅ Download complete.")


if __name__ == "__main__":
    main()
