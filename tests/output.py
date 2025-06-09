import feedparser

from mongo.mongodb_client import db
from mongo.repositories.repository_link_pool import RepositoryLinkPool
from mongo.repositories.repository_daily_trends import RepositoryDailyTrends

repo = RepositoryLinkPool(db)
repodt = RepositoryDailyTrends(db)


def is_urls_processed_already(url):
    is_it = repo.is_link_successfully_processed(url)
    if is_it:
        print(f"{url} it has been processed already. Skipping ")
        return True
    else:
        print(f"{url} it is new ")
        return False


def scrape_wsj_stream():
    rss_url = "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error parsing WSJ RSS feed: {e}")
        return

    for entry in feed.entries:
        summary = entry.get("summary", "").strip()

        if is_urls_processed_already(entry.link.strip()):  # Skip if url in link pool
            continue

        if not summary:
            continue

        repo.insert_link({"url": entry.link.strip(), "is_articles_processed": True})  # Add URL to link pool

        print({
            "title": entry.title.strip(),
            "url": entry.link.strip(),
        })


def locate_link():
    rss_url = "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error parsing WSJ RSS feed: {e}")
        return

    for entry in feed.entries:
        print(repo.delete_links({"url": entry.link}))


def locate_orphan_dt():
    result = repodt.get_daily_trends({})

    for entry in result:
        print(entry.get("sample"))


if __name__ == "__main__":
    locate_orphan_dt()
