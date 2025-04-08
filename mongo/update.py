from pymongo import MongoClient
from dotenv import load_dotenv
import os

# loading env variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
DB_NAME = os.getenv("DB_NAME")
client = MongoClient(MONGO_URI)
db = client[DB_NAME]


def update_articles(selector, update):
    try:
        if selector and update:
            result = db.articles.update_one(selector, update)
        else:
            return False

        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def update_clean_articles(selector, update):
    try:
        if selector and update:
            result = db.clean_articles.update_one(selector, update)
        else:
            return False

        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def update_metadata(selector, update):
    try:
        if selector and update:
            result = db.metadata.update_one(selector, update)
        else:
            return False

        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False


def update_link_pool(selector, update):
    try:
        if selector and update:
            result = db.link_pool.update_one(selector, update)
        else:
            return False
        if result.acknowledged:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error:{e}")
        return False
