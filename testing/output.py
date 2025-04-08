from datetime import time, datetime, UTC
import feedparser

from mongo.find import find_clean_articles, find_articles


def output():
    message = "Hello"

    print(message)


if __name__ == "__main__":
    # Example usage: process articles from batch number 1
    output()
