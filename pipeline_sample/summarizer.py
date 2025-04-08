from transformers import pipeline, BartTokenizer
import re
import torch

UNWANTED_KEYWORDS = ["Copyright", "©", "all rights reserved", "terms of use", "bbc is not responsible", "AP Photo"]

# Correct tokenizer for BART
tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-cnn")
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


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
            if len(chunk) < 200:
                summaries.append(chunk)
            else:
                max_length = 200
                summary = summarizer_pipeline(chunk, max_length=max_length, min_length=80, do_sample=False)[0][
                    "summary_text"]
                summaries.append(summary)

            # 💡 Clear GPU memory if using MPS
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()

        except Exception as e:
            print(f"Error summarizing chunk: {e}")

    # to check if the processed text it is smaller than 512 tokens
    text_processed = "\n".join(summaries)
    token_len = len(tokenizer.encode(text_processed, add_special_tokens=False))

    if token_len > 512:
        smart_summarize(text_processed)
    else:
        return text_processed

