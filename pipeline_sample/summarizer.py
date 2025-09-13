# pipeline_sample/summarizer.py
import os
import re
import torch
from pathlib import Path
from typing import Optional, List

from transformers import pipeline, BartTokenizer, AutoModelForSeq2SeqLM
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"   # TensorFlow: suppress INFO & WARNING
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"  # Optional: quieter MPS fallback
# -------------------------
# Config
# -------------------------
UNWANTED_KEYWORDS = [
    "copyright", "©", "all rights reserved", "terms of use",
    "disclaimer", "reproduction prohibited", "unauthorized reproduction", "no part of this",
    "ap photo", "ap images", "getty images", "reuters", "afp", "associated press",
    "via ap", "image credit", "photo credit", "file photo",
    "bbc is not responsible", "cnn's", "fox news", "nytimes.com", "the guardian",
    "advertisement", "sponsored content", "click here", "read more", "see also", "watch now",
]

HF_HOME = Path(os.getenv("HF_HOME", "models/transformers")).resolve()
MODEL_REPO = "facebook/bart-large-cnn"
MODEL_CACHE_DIRNAME = "models--facebook--bart-large-cnn"  # HF cache naming


# -------------------------
# Device
# -------------------------
def _default_device() -> int:
    if torch.backends.mps.is_available():
        return 0
    if torch.cuda.is_available():
        return 0
    return -1


_DEVICE_DEFAULT = _default_device()

# -------------------------
# Lazy singletons
# -------------------------
_SNAPSHOT_PATH: Optional[Path] = None
_TOKENIZER: Optional[BartTokenizer] = None
_MODEL: Optional[AutoModelForSeq2SeqLM] = None
_PIPELINE = None  # hf pipeline


def _resolve_local_snapshot(base: Path, repo_dirname: str) -> Path:
    """
    Locate the latest snapshot directory for a cached HF model.
    Expect: <HF_HOME>/<repo_dirname>/snapshots/<hash>/
    """
    snapshots_root = base / repo_dirname / "snapshots"
    if not snapshots_root.exists():
        raise RuntimeError(
            f"HF cache not found for '{MODEL_REPO}'. Expected: {snapshots_root}\n"
            f"Run once with internet to cache:\n"
            f"  unset TRANSFORMERS_OFFLINE && export HF_HOME='{HF_HOME}' && "
            f"  python -m pipeline_sample.bootstrap_models"
        )
    candidates = sorted(snapshots_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise RuntimeError(f"No snapshots found under {snapshots_root}")
    return candidates[0]


def _ensure_loaded(device_id: Optional[int] = None) -> None:
    """
    Lazily load snapshot path, tokenizer, model, and pipeline.
    Reuse existing pipeline if device matches; otherwise rebuild on requested device.
    """
    global _SNAPSHOT_PATH, _TOKENIZER, _MODEL, _PIPELINE

    if _SNAPSHOT_PATH is None:
        _SNAPSHOT_PATH = _resolve_local_snapshot(HF_HOME, MODEL_CACHE_DIRNAME)

    if _TOKENIZER is None:
        _TOKENIZER = BartTokenizer.from_pretrained(_SNAPSHOT_PATH)

    if _MODEL is None:
        _MODEL = AutoModelForSeq2SeqLM.from_pretrained(_SNAPSHOT_PATH)

    use_device = _DEVICE_DEFAULT if device_id is None else device_id

    # Rebuild pipeline if missing or device changed
    if _PIPELINE is None or getattr(_PIPELINE, "_device_id", None) != use_device:
        _PIPELINE = pipeline(
            "summarization",
            model=_MODEL,
            tokenizer=_TOKENIZER,
            device=use_device,
            model_kwargs={"torch_dtype": "auto"},
            framework="pt",
        )
        _PIPELINE._device_id = use_device  # stash for reuse


def is_photo_credit(text: str) -> bool:
    return bool(re.search(r"\(AP Photo/.*?\)", text, flags=re.IGNORECASE))


def _choose_device(device: str | int) -> int:
    if device == "auto":
        return _DEVICE_DEFAULT
    try:
        return int(device)
    except Exception:
        return _DEVICE_DEFAULT


def chunk_text(text: str, max_tokens: int = 512) -> List[str]:
    """
    Split into ~token-limited chunks using the real tokenizer.
    """
    _ensure_loaded()  # need tokenizer
    sentences = re.split(r"(?<=[.!?]) +", text)
    chunks: List[str] = []
    current_chunk = ""
    current_len = 0

    for sentence in sentences:
        token_len = len(_TOKENIZER.encode(sentence, add_special_tokens=False))  # type: ignore[arg-type]
        if current_len + token_len > max_tokens:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            current_len = token_len
        else:
            current_chunk += (" " if current_chunk else "") + sentence
            current_len += token_len

    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def smart_summarize(text: str, device: str | int = "auto") -> str:
    """
    Summarize `text` with locally cached BART.
    - Lazy‑loads model/tokenizer/pipeline on first use.
    - If text is short (<200 chars), returns as‑is.
    - Uses chunking + rare recursive pass to keep output <~512 tokens.
    """
    txt = (text or "").strip()
    if len(txt) < 200:
        return txt

    device_id = _choose_device(device)

    # Ensure pipeline is available on the requested device
    _ensure_loaded(device_id=device_id)

    # Safety guard: make sure pipeline/tokenizer exist
    if _PIPELINE is None or _TOKENIZER is None:
        raise RuntimeError("Summarizer pipeline did not initialize correctly. "
                           "Check that the local HF cache exists and HF_HOME is set.")

    chunks = chunk_text(txt)  # this calls _ensure_loaded() too, but we already did it
    summaries: List[str] = []

    for chunk in chunks:
        try:
            input_len = len(_TOKENIZER.encode(chunk, add_special_tokens=False))
            if input_len < 200:
                max_len = max(int(input_len * 0.8), 20)
                min_len = min(10, max_len // 2)
            else:
                max_len = 200
                min_len = 80

            # Either form works once _PIPELINE is set; keep explicit __call__ for clarity
            result = _PIPELINE.__call__(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=False
            )
            summary = result[0]["summary_text"]
            summaries.append(summary)

            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except Exception as e:
            print(f"[summarizer] Error summarizing chunk: {e}")

    text_processed = "\n".join(summaries)
    token_len = len(_TOKENIZER.encode(text_processed, add_special_tokens=False))

    if token_len > 512:
        return smart_summarize(text_processed, device=device_id)

    return text_processed
