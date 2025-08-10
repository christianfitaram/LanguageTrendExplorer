# pipeline_sample/custom_scrapers.py
from __future__ import annotations
from datetime import datetime, UTC
from typing import Dict, Iterable
import requests
import trafilatura
from bs4 import BeautifulSoup
import feedparser


def _fetch_and_extract(url: str) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"Failed to fetch article: {url}, error: {e}")
    return None


def scrape_bbc_stream() -> Iterable[Dict]:
    """Yield BBC articles. No DB writes, no link_pool checks."""
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
        if not full_url:
            continue

        full_text = _fetch_and_extract(full_url)
        if not full_text:
            continue

        yield {
            "title": title,
            "url": full_url,
            "text": full_text,
            "source": "bbc-news",
            "scraped_at": datetime.now(UTC),
        }


def scrape_cnn_stream() -> Iterable[Dict]:
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

        title_tag = link.select_one(".container__headline-text, [data-editable='headline']")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)

        full_text = _fetch_and_extract(full_url)
        if not full_text:
            continue

        yield {
            "title": title,
            "url": full_url,
            "text": full_text,
            "source": "cnn",
            "scraped_at": datetime.now(UTC),
        }


def scrape_wsj_stream() -> Iterable[Dict]:
    rss_url = "https://feeds.a.dj.com/rss/RSSWorldNews.xml"
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        print(f"Error parsing WSJ RSS feed: {e}")
        return

    for entry in feed.entries:
        url = entry.get("link")
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "").strip()
        if not url or not title or not summary:
            continue

        yield {
            "title": title,
            "url": url,
            "text": summary,
            "source": "the-wall-street-journal",
            "scraped_at": datetime.now(UTC),
        }


def scrape_aljazeera() -> Iterable[Dict]:
    import feedparser
    from datetime import datetime, UTC
    feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    for e in feed.entries:
        url = e.get("link")
        title = (e.get("title") or "").strip()
        if not url or not title:
            continue
        text = _fetch_and_extract(url)
        if not text:
            continue
        yield {
            "title": title,
            "url": url,
            "text": text,
            "source": "aljazeera",
            "scraped_at": datetime.now(UTC),
        }

