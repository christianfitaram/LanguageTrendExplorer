import feedparser
import requests
import trafilatura
from bs4 import BeautifulSoup
from datetime import datetime, UTC
from mongo.mongodb_client import db
from mongo.repositories.repository_link_pool import RepositoryLinkPool

repo = RepositoryLinkPool(db)


def fetch_and_extract(url):
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"Failed to fetch article: {url}, error: {e}")
    return None


def is_urls_processed_already(url):
    is_it = repo.is_link_successfully_processed(url)
    if is_it:
        print(f"{url} it has been processed already. Skipping ")
        return True
    else:
        return False


def scrape_bbc_stream():
    url_bbc = "https://www.bbc.com/news"
    try:
        res = requests.get(url_bbc, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Error scraping BBC homepage: {e}")
        return

    for link in soup.select("a[href^='/news'] h2"):
        title = link.get_text(strip=True)
        parent = link.find_parent("a")
        href = parent.get("href") if parent else ""
        full_url = "https://www.bbc.com" + href if href.startswith("/") else href
        if is_urls_processed_already(full_url):
            continue
        full_text = fetch_and_extract(full_url)
        if not full_text:
            continue
        repo.insert_link({"url": full_url})
        yield {
            "title": title,
            "url": full_url,
            "text": full_text,
            "source": "bbc-news",
            "scraped_at": datetime.now(UTC),
        }


def scrape_cnn_stream():
    url_cnn = "https://edition.cnn.com/world"
    try:
        res = requests.get(url_cnn, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
    except Exception as e:
        print(f"Error scraping CNN homepage: {e}")
        return

    for link in soup.select("a[data-link-type='article']"):
        href = link.get("href", "")
        if not href:
            continue
        full_url = "https://edition.cnn.com" + href if href.startswith("/") else href

        if is_urls_processed_already(full_url):
            continue
        full_text = fetch_and_extract(full_url)
        if not full_text:
            continue
        title_tag = link.select_one(".container__headline-text, [data-editable='headline']")
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        full_text = fetch_and_extract(full_url)
        if not full_text:
            continue
        repo.insert_link({"url": full_url})
        yield {
            "title": title,
            "url": full_url,
            "text": full_text,
            "source": "cnn",
            "scraped_at": datetime.now(UTC),
        }


def scrape_wsj_stream():
    rss_url = "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error parsing WSJ RSS feed: {e}")
        return

    for entry in feed.entries:
        summary = entry.get("summary", "").strip()
        if not summary:
            continue

        yield {
            "title": entry.title.strip(),
            "url": entry.link,
            "text": summary,
            "source": "the-wall-street-journal",
            "scraped_at": datetime.now(UTC),
        }
