# train_word2vec.py

from gensim.models import Word2Vec
from mongo.mongodb_client import db
from mongo.repositories.repository_clean_articles import RepositoryCleanArticles
from datetime import datetime, UTC
import os

# ==== CONFIG ====
MODEL_SAVE_PATH = "models/news_word2vec.model"
MIN_NOUN_COUNT = 2  # skip nouns appearing <2 times
VECTOR_SIZE = 100  # dimensions of embeddings
WINDOW_SIZE = 5  # context window
EPOCHS = 5
SKIP_GRAM = 1  # 1 = skip-gram (good for small datasets)

# ==== LOAD DATA ====
repo_clean = RepositoryCleanArticles(db)


def load_noun_corpus():
    corpus = []
    cursor = repo_clean.get_articles({})
    for article in cursor:
        nouns = article.get("nouns", [])
        if nouns:
            corpus.append(nouns)
    print(f"✅ Loaded {len(corpus)} articles with nouns")
    return corpus


# ==== TRAINING ====
def train_and_save_model(corpus):
    model = Word2Vec(
        sentences=corpus,
        vector_size=VECTOR_SIZE,
        window=WINDOW_SIZE,
        min_count=MIN_NOUN_COUNT,
        workers=4,
        sg=SKIP_GRAM,
        epochs=EPOCHS
    )

    # Create directory if missing
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)

    model.save(MODEL_SAVE_PATH)
    print(f"✅ Word2Vec model trained and saved to: {MODEL_SAVE_PATH}")
    return model


# ==== MAIN ====
if __name__ == "__main__":
    print("📦 Starting Word2Vec training...")
    start = datetime.now(UTC)

    corpus = load_noun_corpus()
    if not corpus:
        print("⚠️ No noun data found in MongoDB.")
    else:
        model = train_and_save_model(corpus)

    print(f"🏁 Finished in: {datetime.now(UTC) - start}")
