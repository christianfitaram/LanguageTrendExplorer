# pipeline_sample/summarizer.py
import os
import re
import torch
from pathlib import Path

from transformers import pipeline, BartTokenizer

UNWANTED_KEYWORDS = [
    # Copyright & legal
    "copyright", "©", "all rights reserved", "terms of use",
    "disclaimer", "reproduction prohibited", "unauthorized reproduction", "no part of this",
    # Photo/media credits
    "ap photo", "ap images", "getty images", "reuters", "afp", "associated press",
    "via ap", "image credit", "photo credit", "file photo",
    # Boilerplate & site branding
    "bbc is not responsible", "cnn's", "fox news", "nytimes.com", "the guardian",
    # Misc filler
    "advertisement", "sponsored content", "click here", "read more", "see also", "watch now",
]
MODELS_DIR = Path(os.getenv("HF_HOME", "models/transformers")).resolve()
CACHE_DIR = str(MODELS_DIR)

BART = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(BART, cache_dir=CACHE_DIR, local_files_only=True)

# choose device once
if torch.backends.mps.is_available():
    _device = 0
elif torch.cuda.is_available():
    _device = 0
else:
    _device = -1

_summarizer = pipeline("summarization", model=BART, tokenizer=tokenizer,
                       device=_device, model_kwargs={"torch_dtype": "auto"},
                       framework="pt")


def is_photo_credit(text):
    return bool(re.search(r'\(AP Photo/.*?\)', text, flags=re.IGNORECASE))


def chunk_text(text, max_tokens=512):
    sentences = re.split(r'(?<=[.!?]) +', text)  # Split into sentences while preserving punctuation
    chunks = []
    current_chunk = ""
    current_len = 0

    for sentence in sentences:
        token_len = len(tokenizer.encode(sentence, add_special_tokens=False))
        if current_len + token_len > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            current_len = token_len
        else:
            current_chunk += " " + sentence
            current_len += token_len

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def smart_summarize(text, device="auto"):
    # Skip summarization if text is too short
    if len(text.strip()) < 200:
        return text.strip()

    chunks = chunk_text(text)
    summaries = []
    # Set device: -1 for CPU, or 0 for MPS if available
    if device == "auto":
        if torch.backends.mps.is_available():
            device_id = 0  # MPS
        else:
            device_id = -1  # CPU fallback
    else:
        device_id = device  # allow override

    # Create summarizer on correct device
    summarizer_pipeline = pipeline("summarization", model="facebook/bart-large-cnn", device=device_id)

    for chunk in chunks:
        try:
            input_len = len(tokenizer.encode(chunk, add_special_tokens=False))

            if input_len < 200:
                max_len = max(int(input_len * 0.8), 20)  # at least 20 tokens
                min_len = min(10, max_len // 2)  # min_length smaller but reasonable
            else:
                max_len = 200
                min_len = 80

            summary = summarizer_pipeline(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )[0]["summary_text"]
            summaries.append(summary)

            # Clear GPU memory if using MPS
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        except Exception as e:
            print(f"Error summarizing chunk: {e}")

    # Join summaries and check length again
    text_processed = "\n".join(summaries)
    token_len = len(tokenizer.encode(text_processed, add_special_tokens=False))

    if token_len > 512:
        # If too long, recursively summarize again (but be careful to avoid infinite recursion)
        return smart_summarize(text_processed, device=device)
    else:
        return text_processed
