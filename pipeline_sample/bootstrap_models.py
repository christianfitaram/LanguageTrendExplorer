# pipeline_sample/bootstrap_models.py
"""
Bootstrap Hugging Face models into the local cache so they can be used offline.
Run this ONCE on a machine with internet, before setting TRANSFORMERS_OFFLINE=1.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load .env so HF_HOME / TRANSFORMERS_CACHE are respected
load_dotenv()

# Resolve cache dir
cache_dir = Path(
    os.getenv("HF_HOME", os.getenv("TRANSFORMERS_CACHE", "models/transformers"))
).resolve()

print(f"📦 Caching models into: {cache_dir}")

# List of models you need for exec_gather / classifier
REQUIRED_MODELS = [
    "distilbert-base-uncased-finetuned-sst-2-english",
    "facebook/bart-large-mnli",
    "facebook/bart-large-cnn",  # <-- needed by summarizer
    "sentence-transformers/all-MiniLM-L6-v2",  # <-- needed by embedder

]

# Download each model + tokenizer
for repo in REQUIRED_MODELS:
    print(f"\n⬇️  Downloading & caching: {repo}")
    AutoTokenizer.from_pretrained(repo, cache_dir=str(cache_dir), local_files_only=False)
    AutoModelForSequenceClassification.from_pretrained(repo, cache_dir=str(cache_dir), local_files_only=False)
    print(f"✅ Cached: {repo}")

print("\n🎉 All required models have been cached locally.")
print("You can now set TRANSFORMERS_OFFLINE=1 in your .env and run completely offline.")

