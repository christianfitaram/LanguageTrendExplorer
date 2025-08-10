import os
from datetime import timezone, datetime, UTC

import requests

from custom_pipeline.utils import is_urls_processed_already, fetch_and_extract
from mongo.mongodb_client import db
from mongo.repositories.repository_link_pool import RepositoryLinkPool

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

repo = RepositoryLinkPool(db)
# Your combined OR query for topics
TOPIC_QUERY = (
    "politics OR government OR sports OR athletics OR science OR research OR "
    "technology OR innovation OR health OR medicine OR business OR finance OR "
    "entertainment OR celebrity OR crime OR justice OR climate OR environment OR "
    "education OR schools OR war OR conflict OR travel OR tourism"
)

UNWANTED_CONTENT_SNIPPET = "A required part of this site couldnt load"


def sample_date():
    target_date = datetime.now(UTC).date()  # timezone-aware UTC date
    return target_date


def scrape_newsapi_stream(language='en', page_size=50, target_date=None):
    base_url = "https://newsapi.org/v2/everything"
    if target_date is None:
        target_date = sample_date()
    # We'll fetch two pages to get approx 200 articles
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
                    "apiKey": NEWSAPI_KEY
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"Error fetching news (page {page}): {e}")
            return  # Stops the generator if request fails

        for article in data.get("articles", []):
            # Exclude unwanted content
            content = article.get("content") or ""
            if UNWANTED_CONTENT_SNIPPET in content:
                continue

            url = article.get("url")
            if not url:
                continue
            if is_urls_processed_already(url):
                continue

            full_text = fetch_and_extract(url)
            if full_text is None or not full_text.strip():
                continue  # Skip this article if no content was extracted

            repo.insert_link({"url": url})

            yield {
                "title": article.get("title", "").strip(),
                "text": full_text.strip(),
                "url": url,
                "source": article.get("source", {}).get("name", ""),
                "scraped_at": datetime.now(timezone.utc),
            }


def scrape_all_categories(language='en', page_size=100, pages_per_category=1, target_date=None):
    skipped = 0
    kept = 0
    if target_date is None:
        target_date = sample_date()

    categories = [
        "business",
        "entertainment",
        "general",
        "health",
        "science",
        "sports",
        "technology",
    ]
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
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    print(f"Error fetching category '{category}', page {page}: {e}")
                    continue

                for article in data.get("articles", []):
                    published_at_str = article.get("publishedAt")
                    if not published_at_str:
                        continue

                    try:
                        published_at = datetime.strptime(published_at_str, "%Y-%m-%dT%H:%M:%SZ").date()
                    except ValueError:
                        print(f"❌ Invalid publishedAt format: {published_at_str}")
                        continue

                    if published_at != target_date:
                        print(f"Skipping article from {published_at_str} (wanted {target_date})")
                        skipped += 1
                        continue
                    content = article.get("content") or ""
                    if "A required part of this site couldn't load" in content:
                        continue

                    url = article.get("url")
                    if not url or is_urls_processed_already(url):
                        continue

                    full_text = fetch_and_extract(url)
                    if not full_text or not full_text.strip():
                        continue

                    repo.insert_link({"url": url})
                    kept += 1
                    yield {
                        "title": article.get("title", "").strip(),
                        "text": full_text.strip(),
                        "url": url,
                        "source": article.get("source", {}).get("name", ""),
                        "scraped_at": datetime.now(timezone.utc),
                        "published_at": published_at_str,
                        "category": category
                    }
    finally:
        print(f"✅ Scraped {kept} articles from {target_date}, skipped {skipped} from other dates.")
