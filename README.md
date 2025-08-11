# LanguageTrendExplorer

**LanguageTrendExplorer** is a Python project for exploring linguistic trends in news articles.  
It provides end-to-end tooling to collect, clean, summarise, classify, and analyse textual data.

Articles are scraped from the web, cleaned using **spaCy**, summarised with a **BART-based model**, classified into sentiments and topics using Hugging Face pipelines, and aggregated to surface daily trending nouns.  
Results are persisted in **MongoDB** collections so they can be queried via a simple Flask API or further processed downstream.

The project emphasises **modularity**: each stage of the pipeline (scraping, cleaning, classification, trend analysis) is encapsulated behind service classes or protocols, making it easy to swap in your own scrapers or models without changing the core of the system.

---

## Features

- **Article ingestion and cleaning** – `ArticlesService` orchestrates the ingestion of raw articles, extracts nouns, lemmatises them via spaCy, and stores both raw and cleaned versions in MongoDB collections.
- **Duplicate link handling** – a link pool tracks processed URLs so articles are scraped only once.
- **Batching and sample IDs** – helper functions in `batches.py` and `ids.py` generate unique identifiers (`batch-YYYY-MM-DD`).
- **Summarisation** – uses `facebook/bart-large-cnn` with chunking for long texts.
- **Topic and sentiment classification** – zero-shot and sentiment pipelines from Hugging Face.
- **Daily trend analysis** – counts lemma occurrences and returns the most frequent nouns per topic and sentiment.
- **Repository abstraction** – MongoDB interactions are encapsulated in repository classes.
- **CLI & scripts** – utilities to analyse daily trends, download models, and verify offline model availability.

---

## Architecture Overview

The project is organised into layers:

- **Services** – business logic (`ArticlesService`, `ClassifierService`, `DailyTrendsService`).
- **Repositories** – persistence layer for MongoDB collections.
- **Adapters** – glue code for scrapers and pipelines.
- **Pipelines** – stand-alone modules for summarisation and trend analysis.
- **Use cases** – orchestrators combining services and repositories.
- **Utilities** – validation and safe string operations.
- **Scripts** – developer tools for model management.

---

## Installation

### Prerequisites
- Python 3.9+
- MongoDB
- spaCy + English model (`en_core_web_sm`)
- Hugging Face Transformers + PyTorch

### Step-by-step
```bash
# Clone repository
git clone https://github.com/christianfitaram/LanguageTrendExplorer.git
cd LanguageTrendExplorer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install spacy pymongo flask typer transformers torch datasets

# Download spaCy model
python -m spacy download en_core_web_sm

# Download all transformer models
python scripts/download_all_models.py

# Configure MongoDB in .env
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=language_trends

# (Optional) Run Flask app
python app.py
```

---

## Usage

### 1. Ingest and clean articles
```python
from adapters.scrapers import FunctionScraper
from services.articles import ArticlesService
from services.ids import generate_sample_id

def scrape_my_source():
    for url, html in my_link_iterator():
        yield {
            "url": url,
            "title": parse_title(html),
            "text": parse_text(html),
            "source": "MyNews",
            "published": parse_published(html)
        }

sample_id = generate_sample_id()
scraper = FunctionScraper(scrape_my_source)
service = ArticlesService(articles_repository, clean_articles_repository, metadata_repository)

for article in scraper.stream():
    service.process_article(sample_id, article)
```

---

### 2. Summarise and classify articles
```python
from services.classifier_service import ClassifierService, ArticleIn
from adapters.pipelines import HFPipelines

pipelines = HFPipelines(cache_dir="./models/transformers")
classifier = ClassifierService(pipelines=pipelines)

result = classifier.classify(article_in)
print(result.topic, result.sentiment)
```

---

### 3. Analyse daily trends
```bash
python pipeline_trend_analyzer/main.py --sample-id batch-2025-08-11 --limit 25 --persist
```

---

## Project Structure
```
.
├── adapters/              # Pipelines & scrapers glue code
├── app/                   # Application layer (use cases)
├── lib/                   # Persistence (repositories, MongoDB client)
├── pipeline_sample/       # Summarisation logic
├── pipeline_trend_analyzer/ # CLI for trend analysis
├── scripts/               # Model management scripts
├── services/              # Core business logic
├── utils/                 # Validation & helpers
└── app.py                 # Flask entry point
```

---

## Extending the System
- **Custom topics** – modify `HFPipelines` to pass your own labels.
- **Alternative models** – change summariser or sentiment models in `HFPipelines`.
- **Additional languages** – swap spaCy model in `ArticlesService`.
- **Web API** – extend `app.py` with REST endpoints.

---

## Contributing
Contributions are welcome!  
Please document new features and add tests when submitting a pull request.

---

## License
MIT License

---

## Acknowledgements
- [Hugging Face Transformers](https://huggingface.co)
- [PyTorch](https://pytorch.org)
- [spaCy](https://spacy.io)
- MongoDB
