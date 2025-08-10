# pipeline_sample/news_api_scraper.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from datetime import datetime, UTC, timezone
from typing import Dict, Iterable, Optional

import requests
import trafilatura

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

TOPIC_QUERY = (
    "politics OR government OR sports OR athletics OR science OR research OR "
    "technology OR innovation OR health OR medicine OR business OR finance OR "
    "entertainment OR celebrity OR crime OR justice OR climate OR environment OR "
    "education OR schools OR war OR conflict OR travel OR tourism"
)
UNWANTED_CONTENT_SNIPPET = "A required part of this site couldnt load"


def _get_newsapi_key() -> str:
    # load .env if not already loaded
    load_dotenv()
    key = os.getenv("NEWSAPI_KEY", "").strip()
    if not key:
        raise RuntimeError("NEWSAPI_KEY is missing. Set it in .env or env vars.")
    return key


def _sample_date():
    return datetime.now(UTC).date()


def _fetch_and_extract(url: str) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"Failed to fetch article: {url}, error: {e}")
    return None


def scrape_newsapi_stream(language: str = "en", page_size: int = 50, target_date=None) -> Iterable[Dict]:
    base_url = "https://newsapi.org/v2/everything"
    if target_date is None:
        target_date = _sample_date()

    for page in [1, 2]:
        try:
            response = requests.get(
                base_url,
                params={
                    "q": TOPIC_QUERY,
                    "language": language,
                    "from": target_date,
                    "to": target_date,
                    "sortBy": "publishedAt",
                    "pageSize": page_size,
                    "page": page,
                    "apiKey": NEWSAPI_KEY,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching news (page {page}): {e}")
            return

        for a in data.get("articles", []):
            content = a.get("content") or ""
            if UNWANTED_CONTENT_SNIPPET in content:
                continue
            url = a.get("url")
            if not url:
                continue

            text = _fetch_and_extract(url)
            if not text or not text.strip():
                continue

            yield {
                "title": a.get("title", "").strip(),
                "text": text.strip(),
                "url": url,
                "source": a.get("source", {}).get("name", ""),
                "scraped_at": datetime.now(timezone.utc),
            }


def scrape_all_categories(language: str = "en", page_size: int = 100, pages_per_category: int = 1, target_date=None) -> \
        Iterable[Dict]:
    if target_date is None:
        target_date = _sample_date()

    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    kept, skipped = 0, 0

    try:
        for category in categories:
            for page in range(1, pages_per_category + 1):
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/top-headlines",
                        params={
                            "apiKey": NEWSAPI_KEY,
                            "language": language,
                            "category": category,
                            "pageSize": page_size,
                            "page": page,
                        },
                        timeout=10,
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    print(f"Error fetching category '{category}', page {page}: {e}")
                    continue

                for a in data.get("articles", []):
                    published_at_str = a.get("publishedAt")
                    if not published_at_str:
                        continue
                    try:
                        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ").date()
                    except ValueError:
                        continue
                    if published_at != target_date:
                        skipped += 1
                        continue

                    content = a.get("content") or ""
                    if "A required part of this site couldn't load" in content:
                        continue

                    url = a.get("url")
                    if not url:
                        continue

                    text = _fetch_and_extract(url)
                    if not text or not text.strip():
                        continue

                    kept += 1
                    yield {
                        "title": a.get("title", "").strip(),
                        "text": text.strip(),
                        "url": url,
                        "source": a.get("source", {}).get("name", ""),
                        "scraped_at": datetime.now(timezone.utc),
                        "published_at": published_at_str,
                        "category": category,
                    }
    finally:
        print(f"✅ Scraped {kept} articles from {target_date}, skipped {skipped} from other dates.")
