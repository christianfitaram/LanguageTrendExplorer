from datetime import datetime, UTC

import feedparser
import requests
import trafilatura
from bs4 import BeautifulSoup

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

        if is_urls_processed_already(full_url):  # Skip if url in link pool
            continue

        full_text = fetch_and_extract(full_url)
        if not full_text:
            continue

        repo.insert_link({"url": full_url})  # Add URL to link pool
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

        if is_urls_processed_already(full_url):  # Skip if url in link pool
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

        repo.insert_link({"url": full_url})  # Add URL to link pool
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

        if is_urls_processed_already(entry.link):  # Skip if url in link pool
            continue

        if not summary:
            continue

        repo.insert_link({"url": entry.link})  # Add URL to link pool
        yield {
            "title": entry.title.strip(),
            "url": entry.link,
            "text": summary,
            "source": "the-wall-street-journal",
            "scraped_at": datetime.now(UTC),
        }


def scrape_aljazeera():
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
        repo.insert_link({"url": full_url})  # Add URL to link pool
        yield ({
            "title": link.get_text(strip=True),
            "url": full_url,
            "text": full_text[:200] + "...",
            "source": "aljazeera",
            "scraped_at": datetime.now(UTC),
        })
