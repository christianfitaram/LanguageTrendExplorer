# get_all_articles.py

from custom_pipeline.news_api_scrapper import scrape_newsapi_stream, scrape_all_categories


def get_all_articles():
    seen_urls = set()
    unique_articles = []

    for scrape_func in [scrape_newsapi_stream, scrape_all_categories]:
        articles = scrape_func()
        for article in articles:
            url = article.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

    return unique_articles
