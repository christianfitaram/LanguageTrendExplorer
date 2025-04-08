from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
DB_NAME = os.getenv("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def insert_metadata(document):
    try:
        if not document:
            return "No articles found."

        result = db.metadata.insert_one(document)

        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def insert_sample(document):
    try:
        if not document:
            print("No articles found.")
            return

        result = db.articles.insert_one(document)

        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def insert_clean_articles(document):
    try:
        if not document:
            print("No document found to insert.")
            return
        result = db.clean_articles.insert_one(document)
        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def insert_daily_trends(document):
    try:
        if not document:
            print("No data to insert found.")
            return
        result = db.daily_trends.insert_one(document)
        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def insert_trend_predictions(document):
    try:
        if not document:
            print("No data to insert found.")
            return
        result = db.trend_predictions.insert_one(document)
        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def insert_link_pool(document):
    try:
        if not document:
            return False
        result = db.link_pool.insert_one(document)
        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False
