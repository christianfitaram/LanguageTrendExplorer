# 🌍 Language Trend Explorer

## 🧠 Project Overview

### How it Works:
The program begins by scraping news websites and aggregating article content using tools like Requests, BeautifulSoup, and the NewsAPI. Once collected, the text from each article is processed using NLP libraries such as NLTK and spaCy to tokenize and extract meaningful nouns. These articles are then classified by topic and assigned a sentiment label (positive, neutral, or negative) using AI models built with TensorFlow and scikit-learn.

After classification, the system performs frequency analysis to detect trending terms across all articles. It ranks the top 15 trending words each day and stores the results in MongoDB for tracking and historical analysis. Additionally, the pipeline includes predictive capabilities to forecast emerging trends based on historical data using deep learning techniques.

Technologies Used:
Python, NLTK, spaCy, TensorFlow, scikit-learn, MongoDB, Requests, BeautifulSoup, NewsAPI, among others.

### Use Cases

- 🔍 NLP for language trend detection
- 🗞️ Media monitoring and topic classification
- 📚 Language learning insights from real data
- 📈 Predictive trend analytics with historic article data

### Project structure

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
├── app.py                        # API endpoints
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
pymongo
```

---

## ▶️ How to Use

### Run the Article Scraping & Processing Pipeline:

```bash
cd pipeline_sample
python main.py
```
"NOTE: On the first run, the necessary models will be downloaded, which may take some time."

This will:
- Scrape articles using NewsAPI and custom scrapers
- Clean and preprocess the data
- Classify the article's content
- Summarize long texts
- Pass results to the MongoDB handler (via `insert.py`)


The execution of this pipeline produces 4 types of documents, which are stored in MongoDB.

1. `articles` documents.

   This is the core data of the whole program. This document, combined with others from the same batch, forms the sample to be analyzed for trending words. At this stage is semi-processed, being assigned a topic and sentiment. However, the `text`  still contains stop words (such as "and", "the", "is", etc.) not relevant for the analysis.
   
   <img width="603" alt="Screenshot 2025-04-09 at 09 23 09" src="https://github.com/user-attachments/assets/ed12bdc5-1076-4e16-966d-2e4f852a51a0" />

   Note: ​The most important and biggest part of this document: `text` is obtained by the `fetch_and_extract` function, designed to retrieve and extract the main textual content from a given webpage URL using the `Trafilatura` library. 
  
   Field Descriptions
    
    - `_id`: The unique identifier for the document within the MongoDB collection.
    
    - `title`: The headline or title of the news article.
    
    - `url`: The web address where the original article can be accessed.
    
    - `text`: The full content of the news article. The full text of each article is condensed into a summary using the smart_summarize function. This step ensures that the subsequent analyses are performed on the most pertinent information. (Note: The text field contains the full content of the news article. For computational efficiency during later AI model processing, this text is internally summarized, though the full text is retained in this field.)
    
    - `source`: The origin or publisher of the article, e.g., "CNN".
    
    - `scraped_at`: The timestamp indicating when the article was retrieved or scraped from the source. The presence of "$date" and "$numberLong" suggests that the date is stored in a specific format, likely representing the number of milliseconds since the Unix epoch (January 1, 1970).
    
    - `batch`: An integer denoting the batch number associated with the scraping session. This can be useful for organizing and tracking articles retrieved in the same session.
    
    - `topic`: The summarized text is processed by a zero-shot classification pipeline utilizing the facebook/bart-large-mnli model. In zero-shot classification, the model can assign topics to the text without having seen labeled examples of those topics during training. The model evaluates the likelihood that the text pertains to each candidate topic provided in the `CANDIDATE_TOPICS` list and assigns the most probable topic to the article. 
    
    - `sentiment`: An analysis of the article's sentiment, indicating the overall tone or emotional content. The previous summarized text undergoes sentiment analysis using the `distilbert-base-uncased-finetuned-sst-2-english` model. This model determines the sentiment conveyed in the text, typically categorizing it as positive, negative, or neutral, along with a confidence score indicating the strength of the sentiment. This field is an object containing:
    
        - `label`: A descriptor of the sentiment, such as "NEGATIVE".
    
        - `score`: A numerical value representing the confidence or intensity of the sentiment, with higher absolute values indicating stronger sentiment.

2. `clean_articles` documents

   After all the articles are gathered, the next step is to extract the relevant words for the analysis. These words are stored in an array field named nouns.
   
      <img width="601" alt="Screenshot 2025-04-09 at 10 35 42" src="https://github.com/user-attachments/assets/af2921a0-451b-433d-8f6f-8e12691c66a6" />
 
     ​These documents are the output of the ```clean_articles``` function that processes articles by extracting lemmatized nouns from their text using spaCy's `en_core_web_sm` model. It retrieves unprocessed articles from the   database, extracts relevant nouns, and stores the cleaned data in a separate collection. The function also updates metadata to track the cleaning process's start and end times, ensuring efficient processing and preparation for further analysis.
   

3. `link_pool` documents

   These documents are meant to keep track of what URLs have been scraped, on what batch, and if the scraping process was successful. Designed to track errors and help developers improve scraping methods.
   
     
     <img width="577" alt="Screenshot 2025-04-09 at 10 40 49" src="https://github.com/user-attachments/assets/607c84f8-6d2f-4e6d-987c-74ebf85c58c1" />
     
4. `metadata` documents

   
    <img width="437" alt="Screenshot 2025-04-09 at 10 54 35" src="https://github.com/user-attachments/assets/5e1b9613-36f3-455f-bb73-336cf48dbf0e" />

    This collection serves as a centralized repository for tracking and documenting the various stages and outcomes of data processing tasks. Each document within this collection corresponds to a specific batch of articles and captures detailed information about the processing activities.

    
    Purpose of the `metadata` Collection
    
    - Process Monitoring:** By recording timestamps and counts of processed articles, the collection allows for real-time monitoring of the pipeline's progress and efficiency.
    
    - Performance Analysis:** Storing distributions of topics and sentiments enables analysis of content trends and the effectiveness of classification algorithms.
    
    - Error Tracking:** Documenting unsuccessful processing attempts helps in identifying and addressing issues within the pipeline.
    
    - Historical Reference:** Maintaining records of each batch's processing details provides a historical overview, aiding in audits and long-term analysis.
    
    Key Data Stored in the `metadata` Collection
    
    - Batch Identification:**
    
      - `_id`: A unique identifier for the batch, often combining the batch number and date (e.g., "2-2025-04-08").
    
      - `batch`: The numerical identifier of the batch (e.g., `2`).
    
    - Timestamps:
    
      - `gathering_sample_startedAt` and `gathering_sample_finishedAt`: Timestamps marking the start and end of the article gathering phase.
    
      - `cleaning_sample_startedAt` and `cleaning_sample_finishedAt`: Timestamps for the start and end of the data cleaning phase.
    
      - `analyze_sample_startedAt` and `analyze_sample_finishedAt`: Timestamps indicating when the analysis phase began and ended.
    
    - Processing Outcomes:
    
      - `articles_processed`: An object detailing the count of articles processed successfully and unsuccessfully.
    
    - Distributions:
    
      - `sentiment_distribution`: An array of objects, each representing a sentiment label (e.g., "NEGATIVE") and its corresponding percentage among the processed articles.
    
      - `topic_distribution`: An array similar to `sentiment_distribution`, but for topics like "politics and government," showing the percentage of articles classified under each topic.
    
    - Word Counts:
    
      - `distinct_words`: The number of unique words identified across the processed articles.
    
      - `raw_total_words`: The total count of words before any processing or cleaning.


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

To achieve this, the main function involved is `analyze_sample_trends`

Workflow of `analyze_sample_trends` function:

The `analyze_sample_trends` function is designed to analyze and identify trends within a specific batch of processed articles, focusing on the frequency and context of nouns used. Here's a detailed breakdown of its operation:

1. Retrieve Unprocessed Articles:
   - The function fetches all articles associated with the given `sample_id` that have not yet been processed (`isProcessed: False`).

2. Initialize Analysis:
   - Records the start time of the analysis by updating the corresponding metadata document.

3. Process Each Article:
   - For every retrieved article:
     - Extracts the `topic`, `sentiment` label, and list of `nouns`.
     - Validates the `topic` and `sentiment` to ensure they are meaningful and not placeholders like "unknown" or "none".
     - For each noun, records its occurrence along with its associated topic and sentiment, if valid.
     - Marks the article as processed by setting `isProcessed` to `True` and logs the outcome.

4. Aggregate Word Data:
   - Counts the total occurrences of each noun across all articles.
   - Calculates the total number of words (including duplicates) and the number of distinct words.
   - Updates the metadata with these word count statistics.

5. Analyze Contextual Associations:
   - Groups the collected nouns by their associated topics and sentiments.
   - Determines the distribution of topics and sentiments for each noun.

6. Compile and Store Results:
   - Ranks the top 15 most frequently occurring nouns.
   - For each top noun, compiles its count, rank, and contextual distributions of topics and sentiments.
   - Stores this compiled data in a collection dedicated to tracking daily trends.

7. Finalize Analysis:
   - Records the completion time of the analysis in the metadata.
   - Outputs the results in a tabular format for review.

  ### The output of running `analyze_sample_trends` is the single most important piece of data generated in this program.
  
  Example of a document stored in MongoDB generated after running this part of the pipeline:
  
  ```json
  {
  "_id": "67f18baa1f00644f9bb9fd97",
  "date": "2025-04-04",
  "top_words": [
    {
      "word": "year",
      "count": 279,
      "rank": 1,
      "contexto": {
        "topics": [
          { "label": "climate and environment", "percentage": 10 },
          { "label": "entertainment and celebrity", "percentage": 7 },
          { "label": "war and conflict", "percentage": 13 },
          { "label": "sports and athletics", "percentage": 14 },
          { "label": "health and medicine", "percentage": 13 },
          { "label": "politics and government", "percentage": 10 },
          { "label": "crime and justice", "percentage": 13 },
          { "label": "business and finance", "percentage": 7 },
          { "label": "science and research", "percentage": 10 },
          { "label": "travel and tourism", "percentage": 3 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 50 },
          { "label": "negative", "percentage": 50 }
        ]
      }
    },
    {
      "word": "people",
      "count": 263,
      "rank": 2,
      "contexto": {
        "topics": [
          { "label": "entertainment and celebrity", "percentage": 4 },
          { "label": "technology and innovation", "percentage": 18 },
          { "label": "politics and government", "percentage": 18 },
          { "label": "climate and environment", "percentage": 4 },
          { "label": "science and research", "percentage": 18 },
          { "label": "travel and tourism", "percentage": 11 },
          { "label": "crime and justice", "percentage": 5 },
          { "label": "war and conflict", "percentage": 9 },
          { "label": "business and finance", "percentage": 2 },
          { "label": "sports and athletics", "percentage": 11 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 91 },
          { "label": "negative", "percentage": 9 }
        ]
      }
    },
    {
      "word": "time",
      "count": 107,
      "rank": 3,
      "contexto": {
        "topics": [
          { "label": "business and finance", "percentage": 16 },
          { "label": "entertainment and celebrity", "percentage": 2 },
          { "label": "politics and government", "percentage": 12 },
          { "label": "science and research", "percentage": 7 },
          { "label": "health and medicine", "percentage": 18 },
          { "label": "sports and athletics", "percentage": 4 },
          { "label": "war and conflict", "percentage": 12 },
          { "label": "crime and justice", "percentage": 2 },
          { "label": "climate and environment", "percentage": 12 },
          { "label": "technology and innovation", "percentage": 15 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 23 },
          { "label": "negative", "percentage": 77 }
        ]
      }
    },
    {
      "word": "country",
      "count": 272,
      "rank": 4,
      "contexto": {
        "topics": [
          { "label": "war and conflict", "percentage": 6 },
          { "label": "business and finance", "percentage": 11 },
          { "label": "crime and justice", "percentage": 9 },
          { "label": "travel and tourism", "percentage": 13 },
          { "label": "entertainment and celebrity", "percentage": 2 },
          { "label": "health and medicine", "percentage": 6 },
          { "label": "sports and athletics", "percentage": 15 },
          { "label": "politics and government", "percentage": 17 },
          { "label": "climate and environment", "percentage": 2 },
          { "label": "science and research", "percentage": 19 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 25 },
          { "label": "negative", "percentage": 75 }
        ]
      }
    },
    {
      "word": "day",
      "count": 121,
      "rank": 5,
      "contexto": {
        "topics": [
          { "label": "technology and innovation", "percentage": 8 },
          { "label": "science and research", "percentage": 6 },
          { "label": "crime and justice", "percentage": 4 },
          { "label": "business and finance", "percentage": 14 },
          { "label": "health and medicine", "percentage": 14 },
          { "label": "sports and athletics", "percentage": 20 },
          { "label": "war and conflict", "percentage": 14 },
          { "label": "travel and tourism", "percentage": 4 },
          { "label": "entertainment and celebrity", "percentage": 4 },
          { "label": "politics and government", "percentage": 12 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 86 },
          { "label": "negative", "percentage": 14 }
        ]
      }
    },
    {
      "word": "tariff",
      "count": 256,
      "rank": 6,
      "contexto": {
        "topics": [
          { "label": "crime and justice", "percentage": 3 },
          { "label": "war and conflict", "percentage": 15 },
          { "label": "politics and government", "percentage": 14 },
          { "label": "health and medicine", "percentage": 6 },
          { "label": "travel and tourism", "percentage": 12 },
          { "label": "climate and environment", "percentage": 12 },
          { "label": "science and research", "percentage": 15 },
          { "label": "technology and innovation", "percentage": 3 },
          { "label": "sports and athletics", "percentage": 12 },
          { "label": "entertainment and celebrity", "percentage": 8 }
        ],
        "sentiments": [
          { "label": "positive", "percentage": 33 },
  ```  

## Prediction Feature (BETA)

  Analysis of the prediction.py Script
  
  1. Model Construction
  
       The script defines a function `build_model(window_size)` that constructs an LSTM model with the following architecture:
      
      - An input layer expecting sequences of length equal to `window_size`.
      - An LSTM layer with 32 units to capture temporal dependencies.
      - A dense output layer that produces a single prediction.
      
      The model is compiled using the Adam optimizer and mean squared error (MSE) loss function.
  
  2. Data Retrieval and Preparation
      
      `get_word_time_series(word, min_days=7)`
      
      - Fetches historical daily counts of a specific word from the database.
      - Returns a pandas DataFrame containing dates and counts, ensuring there are at least `min_days` of data.
      
      `prepare_sequences(series, window_size=3)`
      
      - Transforms the time series data into overlapping sequences of length `window_size` for training.
      - Creates input-output pairs where inputs are sequences of `window_size` counts, and outputs are the subsequent count.
  
  3. Training and Prediction
  
      `train_predict(series, window_size=3)`
      
      - Prepares the data sequences.
      - Builds and trains the LSTM model on the prepared sequences for 100 epochs.
      - Predicts the next value in the series using the most recent `window_size` data points.
  
  4. Saving Predictions
      
      `save_prediction(word, predicted_count)`
      
      - Inserts the predicted count for a word into the database.
      - Records the word, the predicted count (rounded to two decimal places), the date for which the prediction is made (typically the next day), and the timestamp of when the prediction was created.
  
  5. Main Execution Flow
  
      `predict_top_words()`
      
      - Builds the LSTM model.
      - Retrieves the most recent daily trend data.
      - Iterates over the top 5 words from the trend data.
        - For each word:
          - Fetches its historical time series data.
          - If sufficient data is available, prepares the sequences.
          - Trains the model and predicts the next day's count.
          - Saves the prediction to the database.
          - Logs the prediction result.
      
      Example of predictions documents generated by this script and stored in MongoDB
      
      <img width="331" alt="Screenshot 2025-04-09 at 11 59 23" src="https://github.com/user-attachments/assets/86536e16-4039-4586-969a-4f9082dbcd05" />

---
## Extras

The `app.py` file, located in the root directory of the project, serves as the entry point for the API layer. It is responsible for configuring and exposing RESTful endpoints that allow external clients to interact with the system via HTTP requests. Users can retrieve processed data through these endpoints, including classified articles, sentiment analysis results, top trending words, and trend predictions. The API is built using Flask - a lightweight web framework-, ensuring efficient and scalable access to the underlying data and analytics.
   
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

## Screenshots

  <img width="812" alt="Screenshot 2025-04-08 at 19 21 38" src="https://github.com/user-attachments/assets/618a9a93-7cf7-4152-ac80-a05bf92dae2f" />
  
  *(CLI output while performing articles scraping and classifying them)*
  
  <img width="812" alt="Screenshot 2025-04-08 at 19 21 38" src="https://github.com/user-attachments/assets/29a0cae2-bf23-42d5-bec8-1faf2b79a1a5" />
  
  *(CLI output after executing the prediction part of the pipeline)*
  
---

## 📫 Contact

**Christian Fita**  
[GitHub: @christianfitaram](https://github.com/christianfitaram)  
Email: *christianfitaram@gmail.com*

---

## 📝 License

MIT License — feel free to fork, modify, and build on it.

---
