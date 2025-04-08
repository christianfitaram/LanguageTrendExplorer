import os
import requests
import trafilatura
from datetime import datetime, UTC
from mongo.insert import insert_link_pool

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
EXCLUDED_SOURCES = {
    "cnn", "bbc-news", "bbc-sport", "the-wall-street-journal", "the-washington-post"
}


def fetch_and_extract(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"Failed to fetch content from {url}: {e}")
    return None


def scrape_newsapi_stream(language='en', page_size=100):
    try:
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={
                "language": language,
                "pageSize": page_size,
                "apiKey": NEWSAPI_KEY
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching news: {e}")
        return  # Stops the generator if request fails

    for article in data.get("articles", []):
        source_id = article.get("source", {}).get("id")
        if source_id in EXCLUDED_SOURCES:
            continue

        url = article.get("url")
        if not url:
            continue

        full_text = fetch_and_extract(url)
        if full_text is None or not full_text.strip():
            continue  # Skip this article if no content was extracted

        insert_link_pool({"url":url})
        yield {
            "title": article.get("title", "").strip(),
            "text": full_text.strip(),
            "url": url,
            "source": article.get("source", {}).get("name", ""),
            "scraped_at": datetime.now(UTC),
        }
