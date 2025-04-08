# 🌍 Language Trend Explorer

A modular NLP pipeline designed to scrape, clean, classify, summarize, analyze, and store trending linguistic content from real-world news sources.

Built for developers and data/AI enthusiasts looking for scalable, cleanly separated pipelines using Python, MongoDB, and modern NLP tools.

---

## 🧠 Project Overview

The **Language Trend Explorer** is split into modular, self-contained components:

- `pipeline_sample`: Scraping, cleaning, classification, summarization
- `pipeline_trend_analyzer`: Analyzing trends, predicting future trends
- `mongo/`: Managing storage in MongoDB (inserts, updates, and queries)

Each pipeline is independently runnable and easily integrable with others.

---

## 📁 Directory Structure

```
LanguageTrendExplorer/
│
├── pipeline_sample/              # Pipeline for scraping and processing articles
│   ├── __init__.py
│   ├── main.py                   # Entry script to run the scraping & processing pipeline
│   ├── classifier.py             # Classifies article content
│   ├── custom_scrapers.py        # Web scrapers for non-API sources
│   ├── exec_cleaner.py           # Cleans scraped text
│   ├── exec_scraper.py           # Orchestrates multiple scrapers
│   ├── news_api_scraper.py       # Uses NewsAPI to get news data
│   └── summarizer.py             # Summarizes long text content
│
├── pipeline_trend_analyzer/      # Performs trend prediction and analysis
│   ├── __init__.py
│   ├── main.py                   # Entry point to analyze stored data
│   ├── prediction.py             # Trend prediction using ML/statistical methods
│   └── trend_analysis.py         # Extracts daily trends and builds frequency maps
│
├── mongo/                        # MongoDB access and operations
│   ├── find.py                   # Queries for stored articles/trends
│   ├── insert.py                 # Inserts processed data into MongoDB
│   └── update.py                 # Updates existing records in MongoDB
│
├── .gitignore                    # Ignore env files, IDE configs, and model weights
├── requirements.txt              # Python dependencies (to be filled)
└── README.md                     # Project documentation (this file)
```

---

## 🔧 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/LanguageTrendExplorer.git
cd LanguageTrendExplorer
```

### 2. Set up the Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

### 3. Install Required Packages

> Create or use a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

Example `requirements.txt`:
```text
requests
beautifulsoup4
nltk
scikit-learn
spacy
openai
pymongo
```

---

## ▶️ How to Use

### Run the Article Scraping & Processing Pipeline:

```bash
cd pipeline_sample
python main.py
```
NOTE: When running this for the first time will download the models used and may take a while.

This will:
- Scrape articles using NewsAPI and custom scrapers
- Clean and preprocess the data
- Classify the article's content
- Summarize long texts
- Pass results to the MongoDB handler (via `insert.py`)

---

### Run the Trend Analysis Pipeline:

```bash
cd pipeline_trend_analyzer
python main.py
```

This will:
- Retrieve processed articles from MongoDB
- Analyze trending nouns
- Predict future trends based on frequency and growth (on beta)
- Store/update trend results

---

## 📦 Environment Variables (If Needed)

If using `.env` files for API keys:

Create a `.env` file at the root:

```dotenv
NEWSAPI_KEY=your_newsapi_key_here
MONGO_URI=mongodb://localhost:27017
```

And load them using `os.environ` or `dotenv`.

---

## 💼 Use Cases

- 🔍 NLP for language trend detection
- 🗞️ Media monitoring and topic classification
- 📚 Language learning insights from real data
- 📈 Predictive trend analytics with historic article data

---

## 📫 Contact

**Christian Ramírez**  
[GitHub: @christianfitaram](https://github.com/christianfitaram)  
Email: *christianfitaram@gmail.com*

---

## 📝 License

MIT License — feel free to fork, modify, and build on it.

---
