import feedparser
from datetime import datetime
from email.utils import parsedate_to_datetime
from pytz import UTC  # or from datetime import timezone as UTC

from custom_pipeline.utils import is_urls_processed_already, fetch_and_extract
from mongo.mongodb_client import db
from mongo.repositories.repository_link_pool import RepositoryLinkPool

repo = RepositoryLinkPool(db)
BLOOMBERG_RSS_FEEDS = {
    "markets": "https://feeds.bloomberg.com/markets/news.rss",
    "politics": "https://feeds.bloomberg.com/politics/news.rss",
    "technology": "https://feeds.bloomberg.com/technology/news.rss",
    "wealth": "https://feeds.bloomberg.com/wealth/news.rss",
}


def scrape_bloomberg_stream_for_date(target_date_str="Fri, 18 Jul 2025"):
    target_date = datetime.strptime(target_date_str, "%a, %d %b %Y").date()

    for category, feed_url in BLOOMBERG_RSS_FEEDS.items():
        print(f"\n📡 Scanning {category} feed...")
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            if not hasattr(entry, "published"):
                continue

            try:
                published_date = parsedate_to_datetime(entry.published).date()
            except Exception as e:
                print(f"Failed to parse date: {entry.published}")
                continue

            if published_date != target_date:
                continue

            url = entry.link
            if not url:
                continue

            if is_urls_processed_already(url):
                continue

            full_text = fetch_and_extract(url)
            if not full_text or not full_text.strip():
                continue

            title = entry.get("title", "").strip()
            if not title:
                continue

            repo.insert_link({"url": url})

            yield {
                "title": title,
                "url": url,
                "text": full_text.strip(),
                "source": "bloomberg",
                "scraped_at": datetime.now(UTC),
            }
