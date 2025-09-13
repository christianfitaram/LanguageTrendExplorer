# pipeline_sample/news_api_scraper.py
from __future__ import annotations
import os
from datetime import datetime, date, UTC, timezone
from typing import Dict, Iterable, Optional, Union

import requests
import trafilatura
from dotenv import load_dotenv

TOPIC_QUERY = (
    "politics OR government OR sports OR athletics OR science OR research OR "
    "technology OR innovation OR health OR medicine OR business OR finance OR "
    "entertainment OR celebrity OR crime OR justice OR climate OR environment OR "
    "education OR schools OR war OR conflict OR travel OR tourism"
)

# Accept both variants seen in the wild
UNWANTED_CONTENT_SNIPPETS = {
    "A required part of this site couldn't load",
    "A required part of this site couldnt load",
}


def _get_newsapi_key() -> str:
    # Load .env every time in case caller didn't load it before importing us
    load_dotenv()
    key = (os.getenv("NEWSAPI_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "NEWSAPI_KEY is missing. Set it in your environment or .env "
            "(e.g. NEWSAPI_KEY=xxxxxxxxxxxxxxxxxxxxxxxx)."
        )
    return key


def _sample_date() -> date:
    return datetime.now(UTC).date()


def _date_param(d: Optional[Union[str, date, datetime]]) -> str:
    """Return YYYY-MM-DD string for NewsAPI 'from'/'to'."""
    if d is None:
        return _sample_date().isoformat()
    if isinstance(d, datetime):
        return d.date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    # assume already a string like 'YYYY-MM-DD'
    return str(d)


def _fetch_and_extract(url: str) -> Optional[str]:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"Failed to fetch article: {url}, error: {e}")
    return None


def scrape_newsapi_stream(
    language: str = "en",
    page_size: int = 50,
    target_date: Optional[Union[str, date, datetime]] = None,
) -> Iterable[Dict]:
    base_url = "https://newsapi.org/v2/everything"
    key = _get_newsapi_key()
    date_str = _date_param(target_date)

    for page in (1, 2):
        try:
            response = requests.get(
                base_url,
                params={
                    "q": TOPIC_QUERY,
                    "language": language,
                    "from": date_str,
                    "to": date_str,
                    "sortBy": "publishedAt",
                    "pageSize": page_size,
                    "page": page,
                    "apiKey": key,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching news (page {page}): {e}")
            return

        for a in data.get("articles", []):
            content = (a.get("content") or "")
            if any(snippet in content for snippet in UNWANTED_CONTENT_SNIPPETS):
                continue

            url = a.get("url")
            if not url:
                continue

            text = _fetch_and_extract(url)
            if not text or not text.strip():
                continue

            yield {
                "title": (a.get("title") or "").strip(),
                "text": text.strip(),
                "url": url,
                "source": a.get("source", {}).get("name", ""),
                "scraped_at": datetime.now(timezone.utc),
            }


def scrape_all_categories(
    language: str = "en",
    page_size: int = 100,
    pages_per_category: int = 1,
    target_date: Optional[Union[str, date, datetime]] = None,
) -> Iterable[Dict]:
    key = _get_newsapi_key()
    target = _date_param(target_date)
    target_dt = datetime.strptime(target, "%Y-%m-%d").date()

    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]
    kept, skipped = 0, 0

    try:
        for category in categories:
            for page in range(1, pages_per_category + 1):
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/top-headlines",
                        params={
                            "apiKey": key,
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

                    if published_at != target_dt:
                        skipped += 1
                        continue

                    content = (a.get("content") or "")
                    if any(snippet in content for snippet in UNWANTED_CONTENT_SNIPPETS):
                        continue

                    url = a.get("url")
                    if not url:
                        continue

                    text = _fetch_and_extract(url)
                    if not text or not text.strip():
                        continue

                    kept += 1
                    yield {
                        "title": (a.get("title") or "").strip(),
                        "text": text.strip(),
                        "url": url,
                        "source": a.get("source", {}).get("name", ""),
                        "scraped_at": datetime.now(timezone.utc),
                        "published_at": published_at_str,
                        "category": category,
                    }
    finally:
        print(f"✅ Scraped {kept} articles from {target_dt}, skipped {skipped} from other dates.")
