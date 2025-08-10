import requests
from bs4 import BeautifulSoup
import feedparser
import trafilatura
from mongo.repositories.repository_link_pool import RepositoryLinkPool
from mongo.mongodb_client import db
from mongo.repositories.repository_articles import RepositoryArticles
from datetime import timezone, datetime, UTC, date
from bson import ObjectId

repo_articles = RepositoryArticles(db)
# List of Bloomberg RSS feeds
BLOOMBERG_RSS_FEEDS = {
    "markets": "https://feeds.bloomberg.com/markets/news.rss",
    "politics": "https://feeds.bloomberg.com/politics/news.rss",
    "technology": "https://feeds.bloomberg.com/technology/news.rss",
    "wealth": "https://feeds.bloomberg.com/wealth/news.rss",
}


def scrap_aljazeera():
    print("Scraping Al Jazeera...")

    base_url = "https://www.aljazeera.com/news/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        res = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Error scraping Al Jazeera homepage: {e}")
        return

    # Look for article links
    links = soup.select("a.u-clickable-card__link")
    print(f"Found {len(links)} article links")

    for link in links:
        href = link.get("href")
        if not href or not href.startswith("/"):
            continue

        full_url = "https://www.aljazeera.com" + href

        # Extract article text
        full_text = fetch_and_extract(full_url)
        if not full_text:
            print(f"❌ Could not extract content from {full_url}")
            continue

        print({
            "title": link.get_text(strip=True),
            "url": full_url,
            "text": full_text[:200] + "...",
            "source": "aljazeera",
            "scraped_at": datetime.now(UTC),
        })


def fetch_and_extract(url):
    downloaded = trafilatura.fetch_url(url)
    return trafilatura.extract(downloaded) if downloaded else None


def scrap_bloomberg_all_feeds():
    for category, feed_url in BLOOMBERG_RSS_FEEDS.items():
        print(f"\n📰 Scraping Bloomberg {category.capitalize()} feed...")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            url = entry.link
            title = entry.title
            published = entry.get("published", "")

            # Extract full article content
            text = fetch_and_extract(url)
            if not text:
                print(f"❌ Failed to extract: {url}")
                continue

            # Preview output
            print({
                "title": title,
                "url": url,
                "text": text[:200] + "...",
                "category": category,
                "source": "bloomberg",
                "scraped_at": datetime.now(UTC),
                "published": published,
            })


def delete_articles():
    repo_link_pool = RepositoryLinkPool(db)

    SAMPLE_ID_TO_DELETE = "2-2025-07-30"

    result = repo_link_pool.collection.delete_many({"in_sample": SAMPLE_ID_TO_DELETE})

    print(f"✅ Deleted {result.deleted_count} documents from link_pool with in_sample = '{SAMPLE_ID_TO_DELETE}'")


def fix_batch_number_for_sample(sample_id, from_batch=2, to_batch=1):
    # Count total articles with the sample ID
    count_total = repo_articles.collection.count_documents({"sample": sample_id})
    print(f"🔎 Total documents with sample '{sample_id}': {count_total}")

    # Update only those with batch = 2
    result = repo_articles.collection.update_many(
        {"sample": sample_id, "batch": from_batch},
        {"$set": {"batch": to_batch}}
    )

    print(f"🛠️ Updated batch from {from_batch} to {to_batch} in {result.modified_count} documents")


def get_next_batch_number():
    # Get today's date
    today = datetime.now(UTC).date()
    today_str = today.strftime("%Y-%m-%d")
    samples = repo_articles.get_distinct_samples(today_str)
    # Get the latest metadata sample (sorted by _id, which is formatted as 'prefix-YYYY-MM-DD')
    batches = []
    for sample in samples:
        parts = sample.split("-")
        if len(parts) >= 4:
            try:
                prefix = int(parts[0])
                batches.append(prefix)
            except (ValueError, IndexError):
                continue
    if len(batches) > 0:
        max_value = max(batches)
        return max_value + 1
    # No samples from today or malformed data
    return 1


if __name__ == "__main__":
    print(get_next_batch_number())
