from custom_scrapers import scrape_bbc_stream, scrape_cnn_stream, scrape_wsj_stream, scrape_aljazeera
from news_api_scraper import scrape_newsapi_stream, scrape_all_categories


def get_all_articles():
    all_articles = []
    seen_urls = set()
    for scrape_func in [scrape_cnn_stream, scrape_bbc_stream, scrape_wsj_stream, scrape_newsapi_stream, scrape_all_categories]:
        for article in scrape_func():
            if article["url"] in seen_urls:
                continue
            seen_urls.add(article["url"])
            all_articles.append(article)
    return all_articles
