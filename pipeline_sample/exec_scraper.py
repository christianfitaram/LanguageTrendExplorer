from custom_scrapers import scrape_bbc_stream, scrape_cnn_stream, scrape_wsj_stream
from news_api_scraper import scrape_newsapi_stream


def get_all_articles():
    all_articles = []
    for scrape_func in [scrape_cnn_stream, scrape_bbc_stream, scrape_wsj_stream, scrape_newsapi_stream]:
        articles = scrape_func()
        all_articles.extend(articles)
    return all_articles
